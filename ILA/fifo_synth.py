import ila
import fifo_def
from fifo_sim import fifo

def synth(m, state, sim):
    print state
    m.synthesize(state, sim)
    ast = m.get_next(state)
    m.exportOne(ast, "ast/" + state + ".ast")

def createFifoILA():
    m = ila.Abstraction("fifo")

    # -------------------------------------------------------------
    # Inputs
    # -------------------------------------------------------------
    cmd     = m.inp("cmd", 3)
    cmdaddr = m.inp("cmdaddr", 64)
    cmddata = m.inp("cmddata", 8)

    # -------------------------------------------------------------
    # Constants
    # -------------------------------------------------------------
    ZERO = m.const(0x0, 8)
    ONE = m.const(0x1, 8)

    # These are the flags that status can output
    STS_VALID           = m.const(fifo_def.STS_VALID, 8)
    STS_DATA_AVAIL      = m.const(fifo_def.STS_DATA_AVAIL, 8)
    STS_DATA_EXPECT     = m.const(fifo_def.STS_DATA_EXPECT, 8)

    # these are the commands that can be written to status
    STS_GO              = m.const(fifo_def.STS_GO, 8)
    STS_COMMAND_READY   = m.const(fifo_def.STS_COMMAND_READY, 8)

    # -------------------------------------------------------------
    # Variable Definitions
    # -------------------------------------------------------------

    # Fifo State
    fifo_state = m.reg("fifo_state", 8)
    m.set_next("fifo_state", ila.choice("fifo_state_choice",
        [ZERO, ONE, ONE+1, ONE+2, ONE+3]))

    # Status register
    fifo_sts = m.reg("fifo_sts", 8)
    m.set_next("fifo_sts", ila.choice("fifo_sts_choice",
        [STS_VALID, STS_VALID | STS_DATA_AVAIL, STS_VALID | STS_DATA_EXPECT, ZERO]))


    # internal index to the FIFO,
    # is amount written so far
    fifo_in_amt  = m.reg("fifo_in_amt", 8)
    m.set_next("fifo_in_amt", ila.choice("fifo_in_amt_choice",
        [fifo_in_amt, fifo_in_amt+1, ZERO]))

    fifo_in_cmdsize = m.reg("fifo_in_cmdsize", 8)
    m.set_next("fifo_in_cmdsize", ila.choice("fifo_in_cmdsize_choice",
        [fifo_in_cmdsize, cmddata, ZERO]))

    # the fifo memory.
    # 256 8 bit registers
    fifo_indata = m.mem("fifo_indata", 8, 8)
    m.set_next("fifo_indata",
            ila.choice("fifo_indata",
                [fifo_indata,
                    ila.store(fifo_indata, fifo_in_amt, cmddata)]))

    # internal index to the FIFO,
    # TODO base this size off of list of command sizes
    fifo_out_amt = m.reg("fifo_out_amt", 8)
    m.set_next("fifo_out_amt", ila.choice("fifo_out_amt_choice",
        [fifo_out_amt, fifo_out_amt-1, ZERO]))

    # The fifo out memory
    # another 256 8 bit registers
    fifo_outdata = m.mem("fifo_outdata", 8, 8)
    m.set_next("fifo_outdata",
                fifo_outdata)

    # dataout
    # this is what is returned by a read or write
    dataout = m.reg("dataout", 8)
    m.set_next("dataout", ila.choice("dataout_choice",
        [ZERO, fifo_outdata[fifo_out_amt], fifo_sts]))

    # -------------------------------------------------------------
    # Decode Logic
    # -------------------------------------------------------------
    addresses = [fifo_def.STS_ADDR, fifo_def.FIFO_ADDR, fifo_def.BURST_ADDR]
    commandData = [fifo_def.STS_COMMAND_READY, fifo_def.STS_GO]

    cmds = [(cmdaddr == fifo_def.STS_ADDR) & (cmd == fifo_def.WR) & (cmddata == d)
            for d in commandData]
    general = [(cmdaddr == a) & (cmd == c) & (fifo_state == s)
            for a in addresses for c in [0,1,2] for s in range(5)]
    m.decode_exprs = general + cmds

    # -------------------------------------------------------------
    # Synthesize
    # -------------------------------------------------------------
    f = fifo()
    sim = lambda s: f.simulate(s)
    for var in f.all_state:
        synth(m, var, sim)

if __name__ == '__main__':
    # ila.setloglevel(1, "")
    createFifoILA()