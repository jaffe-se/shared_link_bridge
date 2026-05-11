# Had to give myself 192.168.200.x subnet alias as kairos is there and can't route to 192.168.0.x I guess
# Command I used was
# sudo ifconfig en0 alias 192.168.200.50 255.255.255.0

KAIROS_IP = "192.168.200.220"

KAIROS_PORT = 4000
LOCAL_PORT = 4220

LOCAL_IP = "192.168.200.10"

declare_myIP_msg = f"ELink|D0, SetIP, {LOCAL_IP}:{LOCAL_PORT}, 4000"

enab_msgs = [
    "ELink|D0, outbound, on",
    "ELink|D0, inbound, on"
]

list_SVs_msgs = [
    "MUI",
    "MUO",
    "N0|T0|Qvideo_mux1|T0|Qveh_start|T0|Qveh_enable|T0|Qveh_motion|T2|Qjoy_steer|T0|Qveh_steer|T0|Qveh_brake|T0|Qveh_throttle|T0|Qveh_shift|T0|Qveh_clutch",
    "L0|T2|QAutoGpsHead|T2|QAutoGpsLat|T2|QAutoGpsLon|T2|QAutoGpsVel|T0|QAutoGpsReferences|T0|QAutoGpsQuality|T2|QAutoGpsStamp|T0|Qpause|T0|Qkey_on|T0|Qeng_enb|T0|Qpe7|T0|Qbbrake|T0|Qfbrake|T2|Qsteerang|T0|Qthrottle|Qsvp_enb_eng|T0|Qserialpck|T0|Qveh_gear|T0|Qveh_state|T0|Qveh_estop|T0|Qveh_obstacle|T2|Qvehicle_bat|T4|Qrun_composite|T4|QVehicleName|T0|QHealth_total|T0|Qrpm|T0|Qfuel|T2|Qsys_thd"
    "MW",
    "ML"
]

# Should respond with something like
# [:AB|N0|Rvideo_mux1|D0|Rveh_start|D0|Rveh_enable|D0|Rveh_motion|D0|Rjoy_steer|D0|Rveh_steer|D0|Rveh_brake|D100|Rveh_throttle|D0|Rveh_shift|D0|Rveh_clutch|D0|C92]
# Not sure if it'll also have that for the quires for KAIROS's outbound variables too 
# this might even be unnecessary and just used to confirm that it is getting the changes

term_msgs = [
    "ELink|D0, outbound, off",
    "ELink|D0, inbound, off"
]

ping_msg = "P0"
pong_msg = "G0"

teleop_start = "EServoPod|D0,TELEOP START"
teleop_stop = "EServoPod|D0,TELEOP STOP"

add_term_msgs = [
    "EPhysics|D0,Stop",
    "EServoPod|D108, 0",
    teleop_stop
]

add_startup_msgs = [
    "\nNO CARRIER"
]

add_teleop_start = [
    "EPhysics|D0,Use ServoPod",
    "EPhysics|D0,Rddf,***********************************",
    teleop_start,
    "EPhysics|D0,Start",
    "EServoPod|D108, 1"
]

beacon_msg = "|".join([
    "rubicon",
    LOCAL_IP,
    "VEH_NorthEastern1",
    "Shepherd_OCU",
    "",
    "0",
    "0",
    "0",
    "0",
    "",
    "0.0.0.0",
    "10-10-2010",
    "10:10:10",
    ""
])

SL_beacon_to_7005 = "[:BA|N0|T4|QVehicleName|DVEH_NorthEastern1|T4|QAutoGpsLat|D0|T4|QAutoGpsLon|D0|T4|QAutoGpsHead|D0|T4|QAutoGpsVel|D0|T4|Qvehicle_bat|D11.8|T4|Qcomputer_bat|D|T4|Qsvp_init|D0|T4|Qsvp_enb_eng|D|T4|Qsvp_start_eng|D0|T4|Qsvp_detether|D|T4|Qpause|D0|T4|Qkey_on|D1|T4|Qs_lights|D0|T4|Qenc2|D0|T4|Qthrottle|D0|T4|Qbbrake|D100|T4|Qfbrake|D0|T4|Qveh_gear|D1|C6E]"