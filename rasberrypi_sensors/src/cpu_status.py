#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Read temperature data measured from DS18B20 through serial
# and publish as ROS topic 


import rospy
import serial
#from datetime import datetime
from std_msgs.msg import String
import subprocess
import os, os.path
from robotx_bionic_msgs.msg import Temperature
import time
from std_msgs.msg import Int32
import pandas as pd
import psutil

global df

class stress_test(object):
        def __init__(self):
                global df
                self.node_name = rospy.get_name()
                rospy.loginfo("[%s] Initializing " %(self.node_name))
                self.temp_pub = rospy.Publisher('~temp', Temperature, queue_size = 10)
                self.size_pub = rospy.Publisher('~size', Int32, queue_size = 10)
                column_names = ['time','cpu_freq','cpu_temperature','throttled','cpuUsage']
                df = pd.DataFrame(columns=column_names)

        def cb(self, no_use):
                global df
                temp_cpu,cpuUsage, cpuFreq = self.get_cpu_temp()
                #size_dir = self.get_dir_size()
                #self.size_pub.publish(size_dir)
		cpu_freq = self.get_clock_freq()
		status = self.get_throttled()                
				
		print(status)		
		#print('cpu status:',throttled_status[status])

                #print datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #print "temperature on cpu: ", str(temp_cpu)
                #print "---------------------"
                temp_msg = Temperature()
                temp_msg.header.stamp = rospy.Time.now()
                temp_msg.temperature_cpu = str(temp_cpu)
                self.temp_pub.publish(temp_msg)
                df = df.append({
                    'time': rospy.Time.now(),
		    'cpu_freq':cpu_freq,
                    'cpu_temperature':str(temp_cpu),
                    'throttled': status,
                    'cpuUsage:' :cpuUsage,
                    },ignore_index=True
                    )

	def get_clock_freq(self):
		# Call command like a command line shell and get the return value
                ret_byte = subprocess.check_output(["vcgencmd", "measure_clock", "arm"])
                # Convert byte to string value, the result is like "frequency(1)=500000992"
                ret_str = ret_byte.decode('utf-8')
                # Cut string from 'equal symbol' to 'degree C symbol', then convert to float
                cpu_freq = float(ret_str[ret_str.find('=')+1: ret_str.find('\'')])
		return cpu_freq

        def get_cpu_temp(self):
                # Call command like a command line shell and get the return value
                ret_byte = subprocess.check_output(["vcgencmd", "measure_temp"])
                # Convert byte to string value, the result is like "temp=48.5'C"
                ret_str = ret_byte.decode('utf-8')
                # Cut string from 'equal symbol' to 'degree C symbol', then convert to float
                cpu_temp = float(ret_str[ret_str.find('=')+1: ret_str.find('\'')])
                print('cpu temperature', cpu_temp)

                cpuUsage = psutil.cpu_percent()
                cpuFreTup= psutil.cpu_freq()
                cpuFreq = cpuFreTup.current
                print('cpuUsage:', cpuUsage)
                print('cpuFreq:', cpuFreq)
                return cpu_temp,cpuUsage, cpuFreq  

        def get_dir_size(self):
                # ret_byte = subprocess.check_output(["ls"])
                # dir_size = ret_byte.count('\n')
                path = '/home/ubuntu/Desktop/Data/data'
	
                dir_size = len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))])

                       
                print('number of extracted data',dir_size)
                return dir_size

	def get_throttled(self):
		# Call command like a command line shell and get the return value
                ret_byte = subprocess.check_output(["vcgencmd", "get_throttled"])
                # Convert byte to string value, the result is like "throttled=0x0"
                ret_str = ret_byte.decode('utf-8')
                # Cut string from 'equal symbol' to 'degree C symbol', then convert to float
                temp = (ret_str[ret_str.find('=')+1: ret_str.find('\'')])
		temp = bin(int(temp, base = 16))
		# '0x20000' -->   '0b100000000000000000'
		# '0x50000' -->  '0b1010000000000000000'

		temp = str(temp)
		temp = temp[temp.find('b')+1:]
		status = int(temp)/(10**18)
		throttled = "--"
		if status > 0:
			throttled = "throttle"
		
		return throttled

        def onShutdown(self):
                df.to_csv('/home/ubuntu/Desktop/stress_test1')
                print(df)
                rospy.loginfo("[%s] Shutdown " %(self.node_name))
                

if __name__ == '__main__':
        rospy.init_node"cpu_status", anonymous = False)
        stress_test_node = stress_test()
        rospy.on_shutdown(stress_test_node.onShutdown)
        rospy.Timer(rospy.Duration(2), stress_test_node.cb)  # 15
        rospy.spin()

