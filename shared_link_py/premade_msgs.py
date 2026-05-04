# Had to give myself 192.168.200.x subnet alias as kairos is there and can't route to 192.168.0.x I guess
# Command I used was
# sudo ifconfig en0 alias 192.168.200.50 255.255.255.0

KAIROS_IP = "192.168.200.220"

KAIROS_PORT = 4000
LOCAL_PORT = 4220

MY_HOST = "192.168.200.50"

declare_myIP_msg = f":BA|ELink|D0, SetIP, {MY_HOST}:{LOCAL_PORT}, 4000|C"

enab_msgs = [
    ":BA|ELink|D0, outbound, on|C",
    ":BA|ELink|D0, inbound, on|C"
]

list_SVs_msgs = [
    ":BA|MUI|C",
    ":BA|MUO|C",
    ":BA|N0|T0|Qvideo_mux1|T0|Qveh_start|T0|Qveh_enable|T0|Qveh_motion|T2|Qjoy_steer|T0|Qveh_steer|T0|Qveh_brake|T0|Qveh_throttle|T0|Qveh_shift|T0|Qveh_clutch|C",
    ":BA|L0|T2|QAutoGpsHead|T2|QAutoGpsLat|T2|QAutoGpsLon|T2|QAutoGpsVel|T0|QAutoGpsReferences|T0|QAutoGpsQuality|T2|QAutoGpsStamp|T0|Qpause|T0|Qkey_on|T0|Qeng_enb|T0|Qpe7|T0|Qbbrake|T0|Qfbrake|T2|Qsteerang|T0|Qthrottle|Qsvp_enb_eng|T0|Qserialpck|T0|Qveh_gear|T0|Qveh_state|T0|Qveh_estop|T0|Qveh_obstacle|T2|Qvehicle_bat|T4|Qrun_composite|T4|QVehicleName|T0|QHealth_total|T0|Qrpm|T0|Qfuel|T2|Qsys_thd|C"
    ":BA|MW|C",
    ":BA|ML|C"
]

# Should respond with something like
# [:AB|N0|Rvideo_mux1|D0|Rveh_start|D0|Rveh_enable|D0|Rveh_motion|D0|Rjoy_steer|D0|Rveh_steer|D0|Rveh_brake|D100|Rveh_throttle|D0|Rveh_shift|D0|Rveh_clutch|D0|C92]
# Not sure if it'll also have that for the quires for KAIROS's outbound variables too 
# this might even be unnecessary and just used to confirm that it is getting the changes

term_msgs = [
    ":BA|ELink|D0, outbound, off|C",
    ":BA|ELink|D0, inbound, off|C"
]

ping_msg = ":BA|P0|C"
pong_msg = ":BA|G0|C"

teleop_start = ":BA|EServoPod|D0,TELEOP START|C"
teleop_stop = ":BA|EServoPod|D0,TELEOP STOP|C"