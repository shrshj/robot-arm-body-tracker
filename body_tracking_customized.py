import cv2
import sys
import pyzed.sl as sl
import ogl_viewer.viewer as gl
import cv_viewer.tracking_viewer as cv_viewer
import socket


class UDP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_message(self,MESSAGE):
        self.socket.sendto(MESSAGE.encode(), (self.ip, self.port))


class Detector:
    def __init__(self,zed,init_params,positional_tracking_parameters,obj_param,obj_runtime_param,udp):
        
        # Camera setting and openning
        self.zed = zed
        self.init_params = init_params
        self.__open_camera()
        
        # Object detection setting
        self.positional_tracking_parameters = positional_tracking_parameters
        self.obj_param = obj_param
        self.obj_runtime_param = obj_runtime_param
        self.camera_info = zed.get_camera_information()
        self.zed.enable_positional_tracking(self.positional_tracking_parameters)
        self.zed.enable_object_detection(self.obj_param)
        
        # Display setting
        self.display_resolution = sl.Resolution(min( self.camera_info.camera_resolution.width, 1280), min( self.camera_info.camera_resolution.height, 720))
        self.image_scale = [self.display_resolution.width /  self.camera_info.camera_resolution.width, self.display_resolution.height /  self.camera_info.camera_resolution.height]
        
        # UDP object for sending data to the robot
        self.udp = udp

        # Body keypoint names for 18 keypoints (YOU SHOULD CHANGE IT IF YOU WANT TO USE 32 LKEYPOINTS)
        self.body_keypoints_name = {
            0: "NOSE",
            1: "NECK",
            2: "RIGHT_SHOULDER",
            3: "RIGHT_ELBOW",
            4: "RIGHT_WRIST",
            5: "LEFT_SHOULDER",
            6: "LEFT_ELBOW",
            7: "LEFT_WRIST",
            8: "RIGHT_HIP",
            9: "RIGHT_KNEE",
            10: "RIGHT_ANKLE",
            11: "LEFT_HIP",
            12: "LEFT_KNEE",
            13: "LEFT_ANKLE",
            14: "RIGHT_EYE",
            15: "LEFT_EYE",
            16: "RIGHT_EAR",
            17: "LEFT_EAR"
        }

        
  
        
    def __open_camera(self):
        if len(sys.argv) == 2:
            filepath = sys.argv[1]
            print("Using SVO file: {0}".format(filepath))
            self.init_params.svo_real_time_mode = True
            self.init_params.set_from_svo_file(filepath)

        # Open the camera
        err = self.zed.open(self.init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            exit(1)
    
    def __close_camera(self):
                
        # Disable modules and close camera
        self.zed.disable_object_detection()
        self.zed.disable_positional_tracking()
        self.zed.close()
        
        
    def find_closeest_body_nose(self,bodies):
        # To-Do
        pass
      
    
    def send_nose_location_over_udp(self,MESSAGE):

        if (len(MESSAGE)>1):
            self.udp.send_message(MESSAGE)
            print("Sent msg --> " + MESSAGE)
            
        else:
            print("Scene is empty!")
    

    def detect(self):
        
        # Create OpenGL viewer
        viewer = gl.GLViewer()
        viewer.init(self.camera_info.calibration_parameters.left_cam, self.obj_param.enable_tracking,self.obj_param.body_format)

        # Create ZED objects filled in the main loop
        bodies = sl.Objects()
        image = sl.Mat()
        
        while viewer.is_available():
            
            # Grab an image
            if self.zed.grab() == sl.ERROR_CODE.SUCCESS:
                    # Retrieve left image
                    self.zed.retrieve_image(image, sl.VIEW.LEFT, sl.MEM.CPU, self.display_resolution)
                    
                    # Retrieve objects
                    self.zed.retrieve_objects(bodies, self.obj_runtime_param)
                    
                    # Find closest body and send it to the robot
                    nose = self.find_closeest_body_nose(bodies)
                    self.send_nose_location_over_udp(nose)

                    # Update GL view
                    viewer.update_view(image, bodies) 
                    
                    # Update OCV view
                    image_left_ocv = image.get_data()
                    
                    cv_viewer.render_2D(image_left_ocv,self.image_scale,bodies.object_list, self.obj_param.enable_tracking, self.obj_param.body_format)
                    cv2.imshow("ZED | 2D View", image_left_ocv)
                    cv2.waitKey(10)

        viewer.exit()
        image.free(sl.MEM.CPU)
        self.__close_camera()
        

if __name__ == "__main__":
        

    # UDP related params
    IP = "192.168.1.185"
    PORT= 5052
    
    
    # Camera and tracking params
    zed = sl.Camera()
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD1080  # Use HD1080 video mode
    init_params.coordinate_units = sl.UNIT.METER          # Set coordinate units
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
    init_params.camera_fps = 15
    
    positional_tracking_parameters = sl.PositionalTrackingParameters()
    
    obj_param = sl.ObjectDetectionParameters()
    obj_param.enable_body_fitting = True            # Smooth skeleton move
    obj_param.enable_tracking = True                # Track people across images flow
    obj_param.detection_model = sl.DETECTION_MODEL.HUMAN_BODY_FAST 
    obj_param.body_format = sl.BODY_FORMAT.POSE_18  # Choose the BODY_FORMAT you need
    
    obj_runtime_param = sl.ObjectDetectionRuntimeParameters()
    obj_runtime_param.detection_confidence_threshold = 40
    
    
    # Tracking started
    print("Running Body Tracking sample ... Press 'q' to quit")
    my_udp = UDP(ip=IP,port=PORT)
    detector = Detector(zed,init_params,positional_tracking_parameters,obj_param,obj_runtime_param,my_udp) 
    detector.detect()
    



    
