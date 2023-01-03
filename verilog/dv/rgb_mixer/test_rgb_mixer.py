import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, with_timeout
from test_encoder import Encoder

clocks_per_phase = 10

@cocotb.test()
async def test_start(dut):
    clock = Clock(dut.clock, 25, units="ns") # 40M
    cocotb.start_soon(clock.start())
    
    dut.RSTB.value = 0
    dut.power1.value = 0;
    dut.power2.value = 0;
    dut.power3.value = 0;
    dut.power4.value = 0;

    await ClockCycles(dut.clock, 8)
    dut.power1.value = 1;
    await ClockCycles(dut.clock, 8)
    dut.power2.value = 1;
    await ClockCycles(dut.clock, 8)
    dut.power3.value = 1;
    await ClockCycles(dut.clock, 8)
    dut.power4.value = 1;

    await ClockCycles(dut.clock, 80)
    dut.RSTB.value = 1

    await with_timeout(RisingEdge(dut.sync), 500, 'us')
    print("rising edge")
    await with_timeout(FallingEdge(dut.sync), 50, 'us')
    print("sync")

async def run_encoder_test(encoder, max_count):
    for i in range(clocks_per_phase * 2 * max_count):
        await encoder.update(1)

    # let noisy transition finish, otherwise can get an extra count
    for i in range(10):
        await encoder.update(0)
    
@cocotb.test()
async def test_all(dut):
    clock = Clock(dut.clock, 10, units="us")
    encoder0 = Encoder(dut.clock, dut.enc0_a, dut.enc0_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)
    encoder1 = Encoder(dut.clock, dut.enc1_a, dut.enc1_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)
    encoder2 = Encoder(dut.clock, dut.enc2_a, dut.enc2_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)

    cocotb.start_soon(clock.start())

    # pwm should all be low at start
    assert dut.pwm0_out == 0
    assert dut.pwm1_out == 0
    assert dut.pwm1_out == 0

    # do 3 ramps for each encoder 
    max_count = 255
    await run_encoder_test(encoder0, max_count)
    await run_encoder_test(encoder1, max_count)
    await run_encoder_test(encoder2, max_count)

    # sync to pwm
    await RisingEdge(dut.pwm0_out)
    # pwm should all be on for max_count 
    for i in range(max_count): 
        assert dut.pwm0_out == 1
        assert dut.pwm1_out == 1
        assert dut.pwm2_out == 1
        await ClockCycles(dut.clock, 1)
