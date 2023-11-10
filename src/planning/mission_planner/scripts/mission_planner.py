#!/usr/local/lib/robot_env/bin/python3

"""
Mission Planner works as follows: 
1. Listens to new task updates from Interface Manager
2. If new task, allocate new task in task queue
3. If tasks in queue, battery health good and system is not performing another task, update next task information
4. Offload task execution to TaskExecutor and monitor progress. 
"""


from collections import deque 
import rospy
from alfred_msgs.msg import DeploymentTask
from enum import Enum
from task_executor import TaskExecutor
from state_manager import TaskType, Emotions, LocationOfInterest, GlobalStates, ObjectOfInterest, VerbalResponseStates, OperationModes



class Mission_Planner():
    
    def __init__(self):
        
        rospy.init_node("mission_planner")

        self.task_queue = deque()

        self.count = 0
        
        self.TaskExecutor = TaskExecutor()
        self.server_updater = ServerUpdater()
              
        self.task_listener = rospy.Subscriber('deployment_task_info', DeploymentTask, self.allocate_task)        # callback: task_allocator
        # self.bat_sub = rospy.Subscriber('/battery', BatteryState, self.battery_check)
        
        # health_client()             # callback: 
        
        
        
    def allocate_task(self, msg):
        """
        Task Allocator adds information regarding the newly added task to the task queue    
        """
        
        print("Just received a new task from the Interface Manager!")
        self.task_queue.append(msg)


    # def battery_check(self, data):
    #     if(int(data.voltage)==0):
    #         self.db.child("battery_state").set(0) #updates firebase to 0 if battery above recommended threshold
    #     else:
    #         self.db.child("battery_state").set(1) #updates firebase to 1 if battery below recommended threshold


    
    def health_manager():
        """
        Health Manager updates battery status (and other health parameters, if applicable) 
        """
        pass


    def update_mission_status(self, result, state):

        print(" ----- MISSION STATUS ----- ", result)

        if not result:
            # Abort mission, update state
            pass
        else:
            self.server_updater.update_emotion(Emotions.HAPPY)
            self.server_updater.currentGlobalState = GlobalStates.REACHED_GOAL
            self.server_updater.update_state()
            
    
        return True


    
            
    def update_next_task(self):
        
        next_task = self.task_queue.popleft()
        
        self.current_task_type = next_task.task_type
        self.current_task_object = next_task.object_type
        self.current_task_resident = next_task.resident_name
        self.current_task_relative = next_task.relative_name
        
        if self.current_task_type == TaskType.DELIVERY.name:

            self.current_task_location_1 = ObjectOfInterest.BOTTLE.name # object pickup location / Enum name (string)
            self.current_task_location_2 = next_task.room_number # / Enum of room_number name (string)

        # elif self.current_task_type = "videocall":
        #     self.current_task_location_1 = next_task.room_number
        #     self.current_task_location_2 = next_task.room_number

        # elif self.current_task_type == "return_home":
        #     self.current_task_location_1 = # home base location
        #     self.current_task_location_2 = None


    def execute_task(self):

        print("Executing next task!", self.count)

        if self.current_task_type == TaskType.DELIVERY.name:
    
            # Navigate to Pick-up Location            
            navSuccess = self.TaskExecutor.navigate_to_location(self.current_task_location_1)
            if not self.update_mission_status(navSuccess):
                return

            print("Reached pick-up location")
            # # Search for and pick-up object
            # manipulationSuccess = manipulate_object()
            # if not self.update_mission_status(manipulationSuccess):
            #     return 


            # Navigate to delivery location
            navSuccess = self.TaskExecutor.navigate_to_location(self.current_task_location_2)
            if not self.update_mission_status(navSuccess):
                return 


            # # Place object at delivery location
            # manipulationSuccess = manipulate_object()
            # if not self.update_mission_status(manipulationSuccess):
            #     return 


        # elif self.current_task_type == "videocall":
        #     navigate_to_location()      # In front of door
        #     wait_for_door_open()
        #     navigate_to_location()      # At videocall spot in room 
        #     align_to_user()
        #     start_videocall()

        # elif self.current_task_type == "return_to_home_base":
        #     pass


        print("Mission Completed")

    def main(self):

        # if not self.battery_health_ok or not self.task_queue or system_state != STATES.IDLE:
        #     print("Cannot perform next task")
    
        rate = rospy.Rate(10)  # 10 Hz, adjust the rate as needed

        while not rospy.is_shutdown():
            if self.task_queue: # and self.system_state == States.IDLE:

                self.update_next_task()
                rospy.sleep(0.1)

                self.execute_task()
                # self.system_state = States.TASK_MODE

            rate.sleep()

            


if __name__ == "__main__":
    
    mission_planner = Mission_Planner()
    
    mission_planner.main()
    
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    
    