cmake_minimum_required(VERSION 3.8)
project(shad_interfaces)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(turtlesim REQUIRED)
find_package(action_msgs REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SensorSample.msg"
  "action/ExploreZone.action"
  DEPENDENCIES std_msgs turtlesim action_msgs
)
ament_export_dependencies(rosidl_default_runtime)
ament_package()
