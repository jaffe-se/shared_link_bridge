cmake_minimum_required(VERSION 3.8)
project(shared_link_py)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/KairosValues.msg"
  "msg/VehicleControl.msg"
  "srv/GetVehicleControl.srv"
  "srv/SetEStopState.srv"
  "srv/SendMsgSet.srv"
)

# already called somewhere caused duplicate error
# ament_python_install_package(${PROJECT_NAME})
install(PROGRAMS
  shared_link_py/shared_link_node.py
  shared_link_py/template_node.py
  shared_link_py/estop_beacon.py
  shared_link_py/other_beacons.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  shared_link_py/UDPConnection.py
  shared_link_py/premade_msgs.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
