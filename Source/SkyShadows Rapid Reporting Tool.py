'''#-------------------------------------------------------------------------------------------------------------------------------------------------#
# Name:        SkyShadow's Rapid Reporting Tool (SRRT.py)
# Purpose:     Rapidy produces WSR and MSE reports and saves them in the clipboard.
# Version:     v2.00
# Author:      Stuart Macintosh, SkyShadow
#
# Created:     29/06/2020
# Copyright:   Open Source
# Licence:     GNU
#-------------------------------------------------------------------------------------------------------------------------------------------------#'''

#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                      Change Log.                                                                   #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
'''
------
v2.00 - 31/01/2022
------
- Updated - SSRT Now uses Gonk for it's input data.

------
v1.08
------
- Feature - Updated to match current MSE Spreadsheet.
- Updated - Misc points to allow for multiple IWATS, INPR and Uniform updates.

------
v1.07
------
- BugFix - urlopen reporting that site certificates have expired.

------
v1.06
------
- BugFix - Not detecting IU courses.
- BugFix - Page Indexing.
- BugFix - FCGH ranks.
- BugFix - Initial FCW.
- BugFix - Comps.
- BugFix - IS-Cx Text.

------
v1.05a
------
- BugFix - Not detecting single LoCs.
- BugFix - Not detecting IS-Cx.

------
v1.04a
------
- Feature - Upgraded to Python 3 / PyQt5.

------
v1.03a
------
- Feature - Removed tracking of Iron Star medals in accordance with new MSE policy. Number of comps is now tracked instead listed as an "X".

------
v1.02a
------

- BugFix - Reviews not spacing out coprrectly due to web rip.
- BugFix - Bug Reports not spacint out correctly due to web rip
- BugFig - Highscores of any kind not being displayed and counting incorrectly
- BugFix - Battles with highscores not being counted
- BugFix - Eliminated the Windows console showing when SRRT.exe is running.
- BugFix - Output text is too small.
- Feature - Icon added to .exe file.
- BugFix - Only one assignment would show in a given period.
- BugFix - Program would crash/infinite loop if a date before a pilot joined the TC was selected.
- BugFix - Removed Misc points for FCHG, CoOP and PVE rating advancements as requested by FA Plif.
- BugFix - App crashed if it found a ATR line with a date but no text.
- BugFix - Improved MSE line copy speed.
- BugFix - MSE line not starting from SP Missions if no SP Missions were flown.
- Feature - MSE Line now displays Date, Rank, Pos and Max Rank so trhat it can be pasted into the first cell on the spreadsheet.
- BugFix - Now shows SP Missions for Flown, Review and Bug reports grouped together instead of individually.
- Feature - Added MoI to MSE line as added MSE Spreadsheets in July 2020.
- BugFix - Calendar dates now reflect 7 days ago to yesterday
------------------------------------------------------------------------------------------------------------------------------------------------------
------
v1.01a
------

- Updated images to have the same background as GUI instead of just black.
- Minor Python code refactoring and formatting.
- Changed the Inpuit box so that it is now editable. The use can now copy to the clipboard and press convert
  OR paste to the input box for long reports spanning multiple pages. The Conver button log changed to reflect the user's selection.
- Fixed a bug where Combat Rating and COOP/PVE Rating ranks weren't displaying properly.
- Removed the old paste into input box and added combo boxes with a date range.
------------------------------------------------------------------------------------------------------------------------------------------------------
------
v1.00a
------

-Initial build.
'''
#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                      Imports.                                                                      #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
import sys, os, urllib.request, configparser
from PyQt5 import QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication, QMainWindow
import resource
from bs4 import BeautifulSoup
import pkgutil
import soupsieve
import resource
import certifi
import ssl
#----------------------------------------------------------------------------------------------------------------------------------------------------#


#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                      Classes.                                                                      #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
class NullDevice():
    '''A object class used to inhibit the SDTOUT/STDERR.'''

    def write(self, s):
        pass
    #------------------------------------------------------------------------------------------------------------------------------------------------#

class SRRTApp(QMainWindow):

    def __init__(self):

        QMainWindow.__init__(self)

        # Config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # Initialise instance variables.
        self.squadrons = []
        self.pilots = []

        # GUI Setup.
        self.ui = uic.loadUi("srrt.ui")
        self.ui.show()

        # Lock the text edits
        self.ui.teOutputWSR.setReadOnly(True)
        self.ui.teOutputMSE.setReadOnly(True)
        self.ui.teOutputMSEMisc.setReadOnly(True)

        # Set the combo boxes.
        self.getSquadrons()
        try:
            defaultSquad = self.ui.cbSquadrons.findText(self.config.get("settings", "defaultSquadron"))
        except configparser.NoSectionError:
            defaultSquad = 0

        self.ui.cbSquadrons.setCurrentIndex(defaultSquad)
        self.cbSquadronsFunc()

        # Set the calendar dates.
        self.ui.calEnd.showToday()
        self.ui.calEnd.setSelectedDate(self.ui.calEnd.selectedDate().addDays(-1))
        self.ui.calStart.setSelectedDate(self.ui.calEnd.selectedDate().addDays(-6))

        # GUI Connections.
        self.ui.actionExit.triggered.connect(closeApp)
        self.ui.btnConvert.clicked.connect(processData)
        self.ui.btnCopyWSR.clicked.connect(copyWSR)
        self.ui.btnCopyMSE.clicked.connect(copyMSE)
        self.ui.btnCopyMSEMisc.clicked.connect(copyMSEMisc)
        self.ui.cbSquadrons.currentIndexChanged.connect(self.cbSquadronsFunc)
        #--------------------------------------------------------------------------------------------------------------------------------------------#


    def getSquadrons(self):

        # Get squadron info from EHTC website.
        try:
            html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php").read()
        except urllib.error.URLError as error:
            if "<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired" in str(error):
                html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php", context=ssl.create_default_context(cafile=certifi.where())).read()
            else:
                raise Exception("SSRT: Connection Error 1")

        data = str(html).split(r"<h2>Squadrons</h2>\n")[1].split(r"<h2>Reserves and Training Units</h2>\n")[0].split("Squadron")

        for squad in data[:-1]:
            sqn = squad.split(r"href=\'/roster.php?")[1]
            info = sqn.split(r"\'>")
            info[1] = info[1] + "Squadron"
            self.squadrons.append(info)

        # Add ther squadron names to the combo box.
        for squad in self.squadrons:
            self.ui.cbSquadrons.addItem(squad[1])
        #--------------------------------------------------------------------------------------------------------------------------------------------#


    def cbSquadronsFunc(self, value=None):

        # Save the new selection as a default.
        try:
            self.config.add_section("settings")
        except configparser.DuplicateSectionError:
            pass

        self.config.set("settings", "defaultSquadron", self.ui.cbSquadrons.currentText())
        with open("config.ini", "w") as configFile:
            self.config.write(configFile)

        # Set the pilots combo box to the squadron's pilots.
        self.ui.cbPilots.clear()
        for pilot in self.getPilots(self.ui.cbSquadrons.currentText()):
            self.ui.cbPilots.addItem(pilot[1])
        #--------------------------------------------------------------------------------------------------------------------------------------------#


    def getPilots(self, strSquadron):
        self.pilots = []
        id = 0

        for squad in self.squadrons:
            if strSquadron == squad[1]:
                id = squad[0]
                break

        try:
            html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php?{squadID}".format(squadID=id)).read()
        except urllib.error.URLError as error:
            if "<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired" in str(error):
                html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php?{squadID}".format(squadID=id), context=ssl.create_default_context(cafile=certifi.where())).read()
            else:
                raise Exception("SSRT: Connection Error 2")

        data = str(html).split("div")

        for pilot in data:
            if r"<a class=\'active pilot\'" in pilot:
                if "Squadron Commander" not in pilot:
                    name = pilot.split(r"type=profile\'>")[1].split(r"</a></mark></")[0]
                    pin, pos = self.getPinPos(pilot, name)
                    self.pilots.append([pin , name, pos])

        return self.pilots
        #--------------------------------------------------------------------------------------------------------------------------------------------#


    def getPinPos(self, pilot, name):
        pin = "0000"


        ref = pilot.split(r"href=\'")[1].split(r"'>")[0][:-1]

        try:
            html = urllib.request.urlopen("https://tc.emperorshammer.org{ref}".format(ref=ref)).read()
        except urllib.error.URLError as error:
            if "<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired" in str(error):
                html = urllib.request.urlopen("https://tc.emperorshammer.org{ref}".format(ref=ref), context=ssl.create_default_context(cafile=certifi.where())).read()
            else:
                raise Exception("SSRT: Connection Error 2")

        name = name.split(" ", 1)[1]
        pin = str(html).split(r'<li class="is-active"><a href="/record.php?pin=')[1].split("&amp;")[0]
        pos = str(html).split(r"addresses.</small>\n")[1].split(name)[0]
        pos = pos.split("<small>")[1].split("-")[0].split(r"/")[0]

        return str(pin), str(pos)
        #--------------------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------------------#


#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                      Functions.                                                                    #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
def closeApp():
    sys.exit()
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def copyWSR():
    deselectAll()
    win.ui.teOutputWSR.selectAll()
    win.ui.teOutputWSR.copy()
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def copyMSE():
    deselectAll()
    win.ui.teOutputMSE.selectAll()
    win.ui.teOutputMSE.copy()
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def copyMSEMisc():
    deselectAll()
    win.ui.teOutputMSEMisc.selectAll()
    win.ui.teOutputMSEMisc.copy()
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def deselectAll():
    # WSR
    cursor = win.ui.teOutputWSR.textCursor()
    cursor.clearSelection()
    win.ui.teOutputWSR.setTextCursor(cursor)

    # MSE
    cursor = win.ui.teOutputMSE.textCursor()
    cursor.clearSelection()
    win.ui.teOutputMSE.setTextCursor(cursor)

    # MSE Misc
    cursor = win.ui.teOutputMSEMisc.textCursor()
    cursor.clearSelection()
    win.ui.teOutputMSEMisc.setTextCursor(cursor)
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def btnInputClearFunc():
    win.ui.teOutputWSR.clear()
    win.ui.teOutputMSE.clear()
    win.ui.teOutputMSEMisc.clear()
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def getTextListFromHtml(url):

    try:
        html = urllib.request.urlopen(url).read()
    except urllib.error.URLError as error:
        if "<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired" in str(error):
            html = urllib.request.urlopen(url, context=ssl.create_default_context(cafile=certifi.where())).read()
        else:
            raise Exception("SSRT: Connection Error 3")

    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def getPilotActivityData(strName):
    # Determine pilot Pin number.
    pin = 0
    for pilot in win.pilots:
        if pilot[1] == strName:
            pin = pilot[0]
            break

    # Retrieve the text from the EHTC website.
    output = []

    startDate = win.ui.calStart.selectedDate()
    strStartDate = str(startDate.year()) + "-" + str(startDate.month()) + "-" + str(startDate.day())
    endDate = win.ui.calEnd.selectedDate()
    strEndDate = str(endDate.year()) + "-" + str(endDate.month()) + "-" + str(endDate.day())

    url = "https://gonk.vercel.app/api/activity?pilotId={pin}&format=text&startDate={startDate}&endDate={endDate}".format(pin=pin, startDate=strStartDate, endDate=strEndDate)
    text = getTextListFromHtml(url)

    # Clean and format the text.
    text = text.replace("*", "")
    text = text.replace("NEW_REPORT:", "")
    text = text.replace("MEDALS_AWARDED:", "")
    text = text.replace("BATTLE_COMPLETED:", "")
    text = text.replace("NEW_UNIFORM_APPROVED:", "")
    text = text.replace("NEW_COMBAT_RATING:", "")
    text = text.replace("SUBMITTED_BATTLE_REVIEW:", "")
    text = text.replace("RANK_SET_BY_TCCOM:", "")
    text = text.replace("IWATS_COMPLETED:", "")
    text = text.replace("SUBMITTED_BATTLE_BUG_REPORT:", "")
    text = text.replace("MEDAL_COUNT_UPDATED:", "")
    text = text.replace("UPDATED_INPR:", "")
    text = text.replace("FLIGHT_CERTIFICATION_WINGS:", "")
    text = text.replace("NEW_COOP_RATING:", "")
    text = text.replace("NEW_PROMOTION:", "")
    text = text.replace("NEW_ASSIGNMENT:", "")
    text = text.replace("UPDATED_ROSTER:", "")
    text = text.replace("IU_COMPLETED:", "")
    text = text.replace("CREATED_BATTLE:", "")
    text = text.replace("SUBMITTED_FICTION:", "")
    text = text.replace("NEW_COMPETITION:", "")
    text = text.replace("OBTAINED_FLIGHT_CERTIFICATION:", "")
    text = text.replace("unknown:", "")
    output = text.split("\n")[3:]

    filteredOutput = []
    for item in output:
        if "Medal count updated by the SOO" in item:
            pass
        else:
            filteredOutput.append(item)
    output = filteredOutput

    return output
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def getPilotCredentials():

    pilotName = win.ui.cbPilots.currentText()

    # Determine pilot Pin number.
    rank = "RANK"
    position = "POSITION"
    for pilot in win.pilots:
        if pilot[1] == pilotName:
            rank = pilot[1].split(" ")[0]
            position = pilot[2]
            break

    # return strRank strPos strMax
    return [rank + "\t", position + "\t", "MAX_RANK\t"]
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def processData():

    # Disable the 'Convert button
    win.ui.btnConvert.setEnabled(False)

    # Initialise variables.
    endDateFound = False
    startDateFound = False
    # Intergers
    lineIndex = 0
    spMissions = 0
    gs = 0
    ss = 0
    bs = 0
    pc = 0
    ism = 0
    iar = 0
    locs = 0
    loss = 0
    ISPR = 0
    ISPW = 0
    ISGR = 0
    ISGW = 0
    ISSR = 0
    ISSW = 0
    ISBR = 0
    ISBW = 0
    ISCR = 0
    ISCW = 0
    dfc = 0
    missHScore = 0
    battHScore = 0
    reports = 0
    reportsDatabased = 0
    reportsOC = 0
    comps = 0
    compsOC = 0
    compsRunDWB = 0
    mois = 0
    fiction = 0
    misc = 0
    reviews = 0
    bugReports = 0
    medals = {}
    iwats = 0
    uniformUpdates = 0
    inprUpdates = 0

    # Strings
    newData = []
    unprocessed = "\n\n-----Lines from Input that SRRT was not able to process:-----\n\n"
    spMissionDict = {}
    spMissiontext = ""
    highscoreText = ""
    fcwText = ""
    fchgText = ""
    combatText = ""
    coopPVEText = ""
    uniformText = ""
    reviewsDict = {}
    reviewText = ""
    bugReportsDict = {}
    bugReportText = ""
    promotionText = ""
    assignmentText = ""
    iwatsText = ""
    inprText = ""
    reportsText = ""
    compsText = ""
    fictionText = ""
    miscText = ""

    # Retrieve the pilots data for the selected pilot in the Pilots: comboBoz.
    data = getPilotActivityData(win.ui.cbPilots.currentText())

# ----------Parse the data for processing.----------
    for line in data:

        if line != "\n":

            # -----SP Missions-----
            if ("Battle completed" in line and "mission" in line) or ("Free mission completed" in line and "mission" in line):

                # MSE Score.
                result = line.split("(")[1]
                result = result.split(" ")[0]
                spMissions += int(result)

                # WSR Text.
                    # Extract ther desired text e.g. TIE-TC 34
                result = line.split(": ")[1]
                result = result.split(" (")[0]

                # Append the mission flown to the spMissionsDict dictionary.
                try:
                    spMissionDict[result.split(" ")[0]] += ", " + result.split(" ")[1]
                except KeyError:
                    spMissionDict[result.split(" ")[0]] = result.split(" ")[1]


                # -----Highscores-----
                if "highscore" in line.lower():
                    # Find the battle/mission completed in the previous line
                    sortieLine = line
                    sortieLine = sortieLine.split(": ")[1]
                    sortieLine = sortieLine.split(" (")
                    battleName = sortieLine[0]

                    # Get the battle's mission count.
                    missions = ""
                    for char in sortieLine[1].split(")")[0]:
                        if char.isdigit():
                            missions += char
                        else:
                            pass
                    battleMissions = int(missions)

                    # Battle and battle mission highscores.
                    if "mission" in line and "battle" in line:
                        result = line.split(", ")
                        missionHighscores = len(result)
                        output = "\nAchieved the highscore in mission(s): "
                        for char in line.split("missions")[1]:
                            if char.isdigit() or char == ",":
                                output += char
                        output += " of battle " + battleName + " and achieved the battle highscore"

                        highscoreText += output
                        battHScore += battleMissions
                        missHScore += missionHighscores

                    # battle mission highscores.
                    elif "highscore(s)" in line.lower():
                        result = line.split(", ")
                        missionHighscores = len(result)
                        output = "\nAchieved the highscore in mission(s): "
                        for char in line.split("missions")[1]:
                            if char.isdigit() or char == ",":
                                output += char
                        output += " of battle " + battleName

                        highscoreText += output
                        missHScore += missionHighscores

                    # -free mission highscores.
                    elif "New mission highscore!" in line:
                        output = "\nAchieved the highscore in " + battleName

                        highscoreText += output
                        missHScore += 1

                    # Error handling:
                    else:
                        newData.append(line)
                        unprocessed += line + "\n"


            # -----Merit Medals-----
            elif "Gold Star" in line and "New award: " not in line:
                gs += 1
            elif "Silver Star" in line and "New award: " not in line:
                ss += 1
            elif "Bronze Star" in line and "New award: " not in line:
                bs += 1
            elif "Palpatine" in line and "New award: " not in line:
                pc += 1
            elif "Imperial Security" in line and "New award: " not in line:
                ism += 1
            elif "Imperial Achievement Ribbon" in line and "New award: " not in line:
                iar += 1


            # -----LoCs-----
            elif "LoC x " in line:
                locs += int(line.replace("LoC x ", ""))

            elif "Legions of Combat (LoC)" in line:
                result = line.split(":")[1]
                result = result.split(" ")[1]
                locs += int(result)

            elif "Legion of Combat (LoC)" in line:
                locs += 1


            # -----LoSs-----
            elif "LoS x " in line:
                loss += int(line.replace("LoS x ", ""))

            elif "Legions of Skirmish (LoS)" in line:
                result = line.split(":")[1]
                result = result.split(" ")[1]
                loss += int(result)

            elif "Legion of Skirmish (LoS)" in line:
                loss += 1


            # -----Iron Stars-----
            elif "IS-" in line:
                result = line
                # Platinum
                if "IS-P" in result:
                    if "IS-PR" in result:
                        ISPR = int(result.split(" x ")[1])
                    elif "IS-PW" in result:
                        ISPW = int(result.split(" x ")[1])
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Gold
                elif "IS-G" in result:
                    if "IS-GR" in result:
                        ISGR = int(result.split(" x ")[1])
                    elif "IS-GW" in result:
                        ISGW = int(result.split(" x ")[1])
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Silver
                elif "IS-S" in result:
                    if "IS-SR" in result:
                        ISSR = int(result.split(" x ")[1])
                    elif "IS-SW" in result:
                        ISSW = int(result.split(" x ")[1])
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Bronze
                elif "IS-B" in result:
                    if "IS-BR" in result:
                        ISBR = int(result.split(" x ")[1])
                    elif "IS-BW" in result:
                        ISBW = int(result.split(" x ")[1])
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Copper
                elif "IS-C" in result:
                    if "IS-CR" in result:
                        ISCR = int(result.split(" x ")[1])
                    elif "IS-CW" in result:
                        ISCW = int(result.split(" x ")[1])
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"


                # Re-add the line if we can't detect the award so this it will be displayed at the bottom of the WSR output.
                else:
                    newData.append(line)
                    unprocessed += line + "\n"


            # ----- Medal of Instruction (MoI)-----
            elif "MoI" in line:
                mois += 1


            # -----Flight Wings-----
            elif "Obtained TIE Corps Flight Certification" in line:
                fcwText += "\nObtained TIE Corps Flight Certification"


            # -----Flight Wings-----
            elif "Flight Certification Wings awarded" in line:
                result = line.split(": ")[1]
                fcwText += "\nAchieved Flight Certification Wings rank of %s"%result.replace("\n", "")


            # -----FCHG Rating-----
            elif "New Fleet Commander's Honor Guard rank achieved" in line:
                result = line.split(": ")[1]
                fchgText += "\nAchieved FCHG rank of %s"%result.replace("\n", "").split("[")[0]


            # -----Combat Rating-----
            elif "New Combat Rating" in line:
                result = line.split(": ")[1]
                combatText += "\nAchieved Combat Rating of %s"%result.replace("\n", "")


            # -----COOP/PVE Rating-----
            elif "New COOP/PVE Rating achieved : " in line:
                result = line.split(": ")[1]
                coopPVEText += "\nAchieved COOP/PVE Rating of %s"%result.replace("\n", "")


            # -----Uniform Update-----
            elif "New uniform upload approved" in line:
                misc += 1
                uniformUpdates += 1
                uniformText = "\nUpdated their uniform %s time(s)"%uniformUpdates


            # -----INPR Update-----
            elif "Updated Imperial Navy Personnel Record (INPR)" in line:
                misc += 1
                inprUpdates += 1
                inprText = "\nUpdated their Imperial Navy Personnel Record (INPR) %s time(s)"%inprUpdates


            # -----Mission Bug Reports-----
            elif "Submitted bug report" in line:

                # Patch bug reports
                if "patch" in line:
                    result = line.split("patch ")[1]

                # Normal bug reports.
                else:
                    # Extract ther desired text e.g. TIE-TC 34
                    try:
                        result = line.split("battle ")[1]
                    except IndexError:
                        result = result

                # Handle unwanted trailing ASCII characters left over for the website rip.
                refinedResullt = ""
                for i in result:
                    if i.isalnum() or i == "-" or i == " ":
                        refinedResullt += i

                # Append the mission review to the bugReportsDict dictionary.
                if "patch" in line:
                    try:
                        bugReportsDict["Patch "] += ", " + refinedResullt.rstrip(":")
                    except KeyError:
                        bugReportsDict["Patch "] = refinedResullt.rstrip(":")

                else:
                    try:
                        bugReportsDict[refinedResullt.split(" ")[0]] += ", " + refinedResullt.split(" ")[1]
                    except KeyError:
                        bugReportsDict[refinedResullt.split(" ")[0]] = refinedResullt.split(" ")[1]

                bugReports += 1
                misc += 1


			# -----Mission reviews-----
            elif "Submitted review for battle" in line:

                # Extract ther desired text e.g. TIE-TC 34
                result = line.split("battle ")[1]

				# Handle unwanted trailing ASCII characters left over for the website rip.
                refinedResullt = ""
                for i in result:
                    if i.isalnum() or i == "-" or i == " ":
                        refinedResullt += i

                # Append the mission review to the reviewsDict dictionary.
                try:
                    reviewsDict[refinedResullt.split(" ")[0]] += ", " + refinedResullt.split(" ")[1]
                except KeyError:
                    reviewsDict[refinedResullt.split(" ")[0]] = refinedResullt.split(" ")[1]

                reviews += 1
                misc += 1


            # -----Other Medals-----
            elif " x " in line:
                result = line.replace("\n", "").split(" x ")
                medalName = result[0]
                medalCount = result[1]
                medals[medalName] = medalCount


            # -----Promotions-----
            elif "new rank set " in line.lower() or "new promotion: " in line.lower():
                result = line.split(": ")[1].replace("\n", "")
                promotionText += "\nPromoted to the rank of %s"%result

            elif "new rank set " in line.lower() or "new promotion : " in line.lower():
                result = line.split(" : ")[1].replace("\n", "")
                promotionText += "\nPromoted to the rank of %s"%result


            # -----Assignments-----
            elif "New assignment :" in line:
                result = line.split(":")[1]
                assignmentText += "\nAssigned to: " + result.replace("\n", "")


            # -----IU Courses.-----
            elif "Course added to Academic Record" in line:
                results = line.replace("[", "").replace("]", "").split(" : ")[1].split(" - ")
                iwatsText += "\nCompleted the IU %s course with a score of %s"%(results[0], results [1].replace("\n", ""))
                iwats += 1
                misc += 1

            # -----Fiction.-----
            elif "New FICTION added by WARD" in line:
                results = line.split("] ")[1]
                fictionText += "\n" + results.replace("FICTION", "fiction")
                fiction += 1
                misc += 1


            # -----Reports-----
            elif "Submitted a new" in line and "report" in line:
                reports += 1
                reportsDatabased += 1
                reportsText = "\nSubmitted x%s reports"%reports


            # -----Competitions-----
            elif "Submitted competition approved" in line:
                comps += 1
                compsText = "\nSubmitted x%s competitons"%comps

            # -----Filter Out Unwanted Lines-----
            elif "UPDATED_UNIT_INFORMATION" in line:
                pass

            elif "Updated unit information for Sin Squadron" in line:
                pass

            elif "Updated the roster information for Sin squadron" in line:
                pass

            elif "NEW_FCHG:" in line:
                pass


            # Write unproccessed lines back to the New Data.txt file.
            else:
                if line != "":
                    newData.append(line)
                    unprocessed += line + "\n"

            # Increment the Input.txt index counter.
            lineIndex += 1
        # --------------------------------------------------


    # ----------Monthly Squadron Evaluation Line.----------
    date = win.ui.calStart.selectedDate().toString("MMMM yyyy") + "\t"
    rank = "\t"
    pos = "\t"
    squad = str(win.ui.cbSquadrons.currentText()).split(" ")[0].title() + "\t"
    moc = "\t"
    maxRank = "\t"
    spare = "\t"

    rank, pos, maxRank = getPilotCredentials()
    scoreLine = date + rank + pos + squad + moc

    # Convert items that equal '0' to nothing.
    scoredItems = [spMissions, locs, loss, "X", missHScore, battHScore, reports,
                   reportsDatabased, reportsOC, comps, compsOC, compsRunDWB, mois, misc]

    for item in scoredItems:
        if item != 0:
            scoreLine += str(item) + "\t"
        else:
            scoreLine += "\t"

    scoreLine = scoreLine[:-1] # Remove the final tab caracter.


    # ----------Weekly Squadron Report Text.----------
    # Final Output.
    if spMissionDict:
        spMissiontext = "\nFlown: " + str(spMissionDict).replace("u'", "").replace("{", "").replace("}", "").replace("'", "")

    if reviewsDict:
        reviewText = "\nWritten reviews for: " + str(reviewsDict).replace("u'", "").replace("{", "").replace("}", "").replace("'", "")

    if bugReportsDict:
        bugReportText = "\nWritten bug reports for: " + str(bugReportsDict).replace("u'", "").replace("{", "").replace("}", "").replace("'", "")

    wsrLine = promotionText + assignmentText + spMissiontext\
              + highscoreText + reviewText + bugReportText + fcwText + fchgText + combatText + coopPVEText + iwatsText + uniformText + inprText + reportsText + compsText + fictionText
    wsrLine = wsrLine.strip("\n") # Removes the leading newline.

    # Merit Medals.
    if gs != 0:
        if gs == 1:
            wsrLine += "\nAwarded x%s Gold Star of the Empire (GS)"%gs
        else:
            wsrLine += "\nAwarded x%s Gold Stars of the Empire (GS)"%gs

    if ss != 0:
        if ss == 1:
            wsrLine += "\nAwarded x%s Silver Star of the Empire (SS)"%ss
        else:
            wsrLine += "\nAwarded x%s Silver Stars of the Empire (SS)"%ss

    if bs != 0:
        if bs == 1:
            wsrLine += "\nAwarded x%s Bronze Star of the Empire (BS)"%bs
        else:
            wsrLine += "\nAwarded x%s Bronze Stars of the Empire (BS)"%bs

    if pc != 0:
        if pc == 1:
            wsrLine += "\nAwarded x%s Palpatine Crescent (PC)"%pc
        else:
            wsrLine += "\nAwarded x%s Palpatine Crescents (PC)"%pc

    if ism != 0:
        if ism == 1:
            wsrLine += "\nAwarded x%s Imperial Security Medal (ISM)"%ism
        else:
            wsrLine += "\nAwarded x%s Imperial Security Medals (ISM)"%ism

    if iar != 0:
        if iar == 1:
            wsrLine += "\nAwarded x%s Imperial Achievement Ribbon (IAR)"%iar
        else:
            wsrLine += "\nAwarded x%s Imperial Achievement Ribbons (IAR)"%iar

    # LoCs
    if locs != 0:
        if locs == 1:
            wsrLine += "\nAwarded x%s Legion of Combat (LoC)"%locs
        else:
            wsrLine += "\nAwarded x%s Legions of Combat (LoCs)"%locs

    # LoSs
    if loss != 0:
        if loss == 1:
            wsrLine += "\nAwarded x%s Legion of Skirmish (LoS)"%loss
        else:
            wsrLine += "\nAwarded x%s Legions of Skirmish (LoSs)"%loss


    #---------- Ion Stars ----------
    # Platinum
    if ISPR != 0:
        wsrLine += "\nAwarded %sx Iron Star with Platinum Ribbon (IS-PR)"%ISPR

    if ISPW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Platinum Wings (IS-PW)"%ISPW

    # Gold
    if ISGR != 0:
        wsrLine += "\nAwarded %sx Iron Star with Gold Ribbon (IS-GR)"%ISGR

    if ISGW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Gold Wings (IS-GW)"%ISGW

    # Silver
    if ISSR != 0:
        wsrLine += "\nAwarded %sx Iron Star with Silver Ribbon (IS-SR)"%ISSR

    if ISSW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Silver Wings (IS-SW)"%ISSW

    # Bronze
    if ISBR != 0:
        wsrLine += "\nAwarded %sx Iron Star with Bronze Ribbon (IS-BR)"%ISBR

    if ISBW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Bronze Wings (IS-BW)"%ISBW

    # Copper
    if ISCR != 0:
        wsrLine += "\nAwarded %sx Iron Star with Copper Ribbon (IS-CR)"%ISCR

    if ISCW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Copper Wings (IS-CW)"%ISCW


    # ---------- Other Medals ----------
    for medal in medals:
        wsrLine += "\nAwarded %sx %s"%(medals[medal], medal)


    # ----------Misc text.----------
    if reviews != 0:
        miscText += "\n{0}x point(s) for writing {0}x review(s)".format(reviews)

    if bugReports != 0:
        miscText += "\n{0}x point(s) for writing {0}x bug repor(s)".format(bugReports)

    if uniformUpdates != 0:
        miscText += "\n{0}x point(s) for updating their uniform {0}x time(s)".format(uniformUpdates)

    if inprUpdates != 0:
        miscText += "\n{0}x point(s) for updating their INPR {0}x time(s)".format(inprUpdates)

    if iwats != 0:
        miscText += "\n{0}x point(s) for completing {0}x IWATS course(s)".format(iwats)

    if fiction != 0:
        miscText += "\n???x point(s) for writing {0}x fiction(s)".format(fiction)


    # Unprocessed results handling
    unprocOut = ""
    if unprocessed == "\n\n-----Lines from Input that SRRT was not able to process:-----\n\n":
        pass
    else:
        unprocOut = unprocessed


    # Write to the outputs.
    win.ui.teOutputWSR.setText(wsrLine + unprocOut)
    win.ui.teOutputMSE.setText(scoreLine)
    win.ui.teOutputMSEMisc.setText(miscText[1:])

    # Enable the 'Convert button
    win.ui.btnConvert.setEnabled(True)
    #------------------------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------------------#



#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                     Main Program.                                                                  #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
# Inhibit the STDOUT and STDERR so we don't get the annoying pop up window when we close the app.
##sys.stdout = NullDevice()
##sys.stderr = NullDevice()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	win = SRRTApp()
	sys.exit(app.exec_())
#----------------------------------------------------------------------------------------------------------------------------------------------------#
