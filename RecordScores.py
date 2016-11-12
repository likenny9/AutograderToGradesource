### UCSD AutoGrader to GradeSource
### Converts scores for CSE 3 from AutoGrader into grades in GradeSource
### Author: Kenny Li
### Created: Nov 12, 2016

###TODO: Format each function to be independent, so that uploading to GradeSource can be done with a typical CSV

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

import getpass
import requests
from lxml import html
from lxml import etree

import signal
import sys

#Adapter for the requests module to read TLSv1
class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

#Scrapes autograder and outputs two lists of names of individuals who got 0 and who got 5
def scrapeAutograder():

	print("--Autograder to Gradesource Script--\nCTRL+C to quit anytime.\n")

	#Allows session to close when done
	with requests.session() as session:

		AG_LOGIN_URL = 'https://autograder.ucsd.edu/login'
		site = session.get(AG_LOGIN_URL)
		tree = html.fromstring(site.text)
		auth_token = list(set(tree.xpath("//input[@name='authenticityToken']/@value")))[0]

		#Log In
		while True:
			credentials = {
				"username": input("Autograder email: "),
				"password": getpass.getpass("Password: "),
				"authenticityToken": auth_token
			}

			#Log In
			result = session.post(AG_LOGIN_URL, data = credentials, headers = dict(referer = AG_LOGIN_URL))

			#Invalid credentials if redirect to login page
			if result.url == AG_LOGIN_URL:
				print("Invalid username or password. Try again.")
			else:
				break

		print("\nLogged In Successfully!")
		#Get course (e.g. CSE 3 - Fall 2016)
		while True:
			AG_COURSE_NUM = input("Please enter Course Number: ")
			AG_COURSE_HOME_URL = "https://autograder.ucsd.edu/?courseId={0}".format(AG_COURSE_NUM)

			#Try going to the specified course
			try:
				result = session.get(AG_COURSE_HOME_URL, headers = dict(referer = AG_COURSE_HOME_URL))
				tree = html.fromstring(result.content)
				print("Course: " + tree.xpath("//option/@title")[0])
				proceed = input("\nDo you wish to proceed? [y/n]: ")
				if proceed == 'y':
					break
			#Not an accessible course
			except IndexError:
				print("You are not allowed to access this course.  Please make sure you have the correct course number.")

		#Get assignment(e.g. LAB7/HW6)
		while True:
			AG_ASSIGN_NUM = input("Please enter Assignment Number: ")
			AG_ASSIGN_URL = "https://autograder.ucsd.edu/graderconsole/students/{0}?assignmentId={1}".format(AG_COURSE_NUM,AG_ASSIGN_NUM)

			#Try going to the specified assignment
			try:
				result = session.get(AG_ASSIGN_URL, headers = dict(referer = AG_ASSIGN_URL))
				tree = html.fromstring(result.content)
				print("Assignment: " + tree.xpath("//select[@id='assignments']/option[@value={0}]/text()".format(AG_ASSIGN_NUM))[0])
				proceed = input("\nDo you wish to proceed? [y/n]: ")
				if proceed == 'y':
					break
			#Not a valid assignment
			except IndexError:
				print("This assignment does not exist.  Please make sure you have the correct assignment number.")

		#Gets all last names with a score of 0/10
		score_zeros_last = tree.xpath("//tr[@class='bg-red']/td[position()=2]/text()")
		#Gets all first names with a score of 0/10
		score_zeros_first = tree.xpath("//tr[@class='bg-red']/td[position()=1]/text()")
		#Gets all last names with a score of 5/10
		score_halves_last = tree.xpath("//tr[@class='bg-blue']/td[position()=2]/text()")
		#Gets all first names with a score of 5/10
		score_halves_first = tree.xpath("//tr[@class='bg-blue']/td[position()=1]/text()")


		#ZEROS: Puts first names as a list in a list
		list_of_zeros = []
		for first_name in score_zeros_last:
			list_of_zeros.append([first_name])


		#ZEROS: Adds the last names with the respective first names in the list
		name_index = 0
		for name_list in list_of_zeros:
			for last_name in score_zeros_first:
				name_list.append(score_zeros_first[name_index])
				name_index+=1
				break

		#Print names of zeros
		print("\nThese students got a score of 0:")
		for namepair in list_of_zeros:
			print(namepair[0] + ", " + namepair[1])

		#HALF SCORES: Puts first names as a list in a list
		list_of_halves = []
		for first_name in score_halves_last:
			list_of_halves.append([first_name])

		#HALF SCORES: Adds the last names with the respective first names in the list
		name_index = 0
		for name_list in list_of_halves:
			for last_name in score_halves_first:
				name_list.append(score_halves_first[name_index])
				name_index+=1
				break

		#Print names of half credit scores
		print("\nThese students got a score of 5:")
		for namepair in list_of_halves:
			print(namepair[0] + ", " + namepair[1])

		print("\nAll other students will the receive full credit of 10:")

		#Got the list, time to upload
		while True:
			proceed = input("\nUpload to GradeSource? [y/n]: ")
			if proceed == 'y':
				uploadToGradeSource(list_of_zeros,list_of_halves)
				break

#Uploads grades to gradesource, giving 0s (as blanks), 5s, and 10s
def uploadToGradeSource(zeros,halves):

	#Allows session to close when done
	with requests.session() as session:
		#Gradesource is using TSLv1
		session.mount('https://', MyAdapter())

		#Log In
		while True:
			credentials = {
				"User": input("Gradesource username: "),
				"Password": getpass.getpass("Password: "),
			}

			GS_VALIDATE_URL = 'https://gradesource.com/validate.asp'
			GS_LOGIN_URL = 'https://gradesource.com/login.asp'
			result = session.post(GS_VALIDATE_URL, data = credentials, headers = dict(referer = GS_VALIDATE_URL), verify=None)

			#Invalid credentials if redirect to login page
			if result.url == GS_LOGIN_URL:
				print("Invalid username or password. Try again.")
			else:
				break

		print("\nLogged In Successfully!")

		#Get course (e.g. CSE 3 - Fall 2016)
		while True:
			GS_COURSE_NUM = input("Please enter Course Number [Enter for Default] : ")
			######GS_ASSIGN_NUM = 0
			GS_COURSE_URL = "https://www.gradesource.com/selectcourse.asp?id={0}".format(GS_COURSE_NUM)

			#Try going to the specified course
			try:
				result = session.get(GS_COURSE_URL, headers = dict(referer = GS_COURSE_URL))
				tree = html.fromstring(result.content)
				courseName = tree.xpath("//td/b/text()")[0]
				print("Course: " + courseName)
				proceed = input("\nDo you wish to proceed? [y/n]: ")
				if proceed == 'y':
					break
			#Not an accessible course
			except IndexError:
				print("You are not allowed to access this course.  Please make sure you have the correct course number.")

		#Get assignment (e.g. LAB7/HW6)
		while True:
			GS_ASSIGN_NUM = input("Please enter Assignment Number: ")
			GS_ASSIGN_URL = "https://www.gradesource.com/editscores1.asp?id={0}".format(GS_ASSIGN_NUM)

			#Try going to the specified assignment
			try:
				result = session.get(GS_ASSIGN_URL, headers = dict(referer = GS_ASSIGN_URL))
				tree = html.fromstring(result.content)
				assignName = tree.xpath("//td[@class='MT']/font/b/text()")[1]
				print("Assignment: " + assignName)
				proceed = input("\nDo you wish to proceed? [y/n]: ")
				if proceed == 'y':
					break
			#Not a valid assignment
			except IndexError:
				print("This assignment does not exist.  Please make sure you have the correct assignment number.")
		
		#Gets Last Name, First Name of all students
		gsnames = tree.xpath("//td[@class='BT'][position()=1]/text()")
		#Gets the grade input box of each student
		gsfield = tree.xpath("//td[@class='BT'][position()=3]/input[position()=1]")
		#Gets the hidden id value of each student
		gsids = tree.xpath("//td[@class='BT'][position()=3]/input[position()=2]")
		
		#Final object to hold all grades to submit
		grades = {}
		#Temp object to gather all the hidden student ids
		studentnums = {}

		#Adds all id# with values to the studentnums object
		for item in gsids:
			studentnums[item.name] = item.value


		#There are already scores for the assignment
		existingScoresWarning = True;

		#Goes through names and inputs matching names with the appropriate grade
		for name in gsnames:

			#Adds the blanks to grades object
			for namelist in zeros:
				#Gradesource name includes middle name but autograder does not
				if namelist[0] + ", " + namelist[1] in name.lstrip():
					grades[gsfield[gsnames.index(name)-4].name] = ""
					zeros.remove(namelist)
					break

			#Adds the 5s to grades object
			for namelist in halves:
				if namelist[0] + ", " + namelist[1] in name.lstrip():
					#Need to shift by 4 because of the extra 4 inputs in the beginning
					grades[gsfield[gsnames.index(name)-4].name] = int(u'\u0035')
					halves.remove(namelist)
					break

			#if there are scores of 10 already and we haven't disabled the warning
			if gsfield[gsnames.index(name)-4].value == "10" and existingScoresWarning:
				while True:
					print("\nThere already existing scores for this assignment.")
					proceed = input("Input y to proceed. Else Ctrl + c to exit the program: ")
					if proceed == 'y':
						existingScoresWarning = False
						break;

			#If we didn't already give a blank or a 5, then give a 10
			elif not gsfield[gsnames.index(name)-4].name in grades:
				grades[gsfield[gsnames.index(name)-4].name] = int(u'\u0031' + u'\u0030')

		#Merge student ids with student grades
		grades.update(studentnums)
		
		#Students not in Gradesource
		print("\nThe following students are in Autograder, but not Gradesource.")
		for name in zeros:
			print(name[0] + ", " + name[1])
		for name in halves:
			print(name[0] + ", " + name[1])
		#Make sure user understand these students are not in Gradesource
		while True:
			proceed = input("\nConfirm this is ok? [y/n]:")
			if proceed == 'y':
				break
		
		#Adds assessmentId to submit (this is a name attribute in the HTML)
		grades['assessmentId'] = tree.xpath("//input[@name='assessmentId']/@value")[0]
		#Adds studentCount to submit (this is a name attribute in the HTML)
		grades['studentCount'] = tree.xpath("//input[@name='studentCount']/@value")[0]

		#Final confirmation for submission of grade
		print("\n--- List of Students and Grades for Assignment " + assignName + " --- ")
		for name in gsnames[4:]:
			print(name + " " + str(grades[gsfield[gsnames.index(name)-4].name]))
		print("--- List of Students and Grades for Assignment " + assignName + " --- ")

		while True:
			proceed = input("\nYou are submitting grades for " + courseName + " " + assignName + 
				"\nWarning: Grades will be permanently changed in GradeSource.\nFinal Confirmation: Submit Grades? [y/n]: ")
			if proceed == 'y':
				break		

		GS_SUBMIT_URL = 'https://www.gradesource.com/updatescores1.asp'
		
		#To submit, we need to include in the grades object:
		# { 'student#' : grade, 'id#' : value, 'assessmentId' : value, 'studentCount' : count}
		# WARNING: THIS WILL CHANGE GRADES. MAKE SURE YOU KNOW WHAT YOU'RE DOING.
		result = session.post(GS_SUBMIT_URL, data = grades)

		print("\nSubmission Successful!\n")


#Handles a graceful CTRL+C
def exitProgram(signal, frame):
	print("\nQuiting program... Done\n")
	sys.exit(0)

#Start program
if __name__ == '__main__':
	signal.signal(signal.SIGINT, exitProgram)
	scrapeAutograder()
