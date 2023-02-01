execute_process(COMMAND "/home/nivanpc/RSSGroupProject/catkin_ws/build/rosbot_ros/src/rosbot_description/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/nivanpc/RSSGroupProject/catkin_ws/build/rosbot_ros/src/rosbot_description/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
