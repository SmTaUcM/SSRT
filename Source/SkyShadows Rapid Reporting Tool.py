'''#-------------------------------------------------------------------------------------------------------------------------------------------------#
# Name:        SkyShadow's Rapid Reporting Tool (SRRT.py)
# Purpose:     Rapidy produces WSR and MSE reports and saves them in the clipboard.
# Version:     v1.03a
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
        html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php").read()

        data = str(html).split(">Squadrons<")[1].split("daedalus.php")[0].split("type=sqn")
        for squad in data:
            if "Squadron" in squad:
                info = squad.replace("&", "").split("</a>")[0].replace("id=", "").split('">')
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

        html = urllib.request.urlopen("https://tc.emperorshammer.org/roster.php?type=sqn&id={squadID}".format(squadID=id)).read()
        data = str(html).split("uniform patch")[1].split("SQUADRON CITATIONS EARNED")[0].split("<br>")

        for line in data:
            if "profile" in line:
                self.pilots.append(line.split(".php?")[1].replace("</a>", "").split("</td>")[0].replace("pin=", "").split('&type=profile">'))
        return self.pilots
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

    html = urllib.request.urlopen(url).read()
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
    lastPage = ""
    webPage = 0
    endDateFound = False
    startDateFound = False
    output = []

    while not (endDateFound and startDateFound):

        if webPage == 0:
            page = ""
        else:
            page = "&start=%s01"%str(webPage)

        url = "https://tc.emperorshammer.org/record.php?pin={pin}&type=atr{page}".format(pin=pin, page=page)
        text = getTextListFromHtml(url)

        # Check to see if we are still getting new data from the EH website - prevents infinite search loop.
        if text == lastPage:
            break
        else:
            lastPage = text

        # Process the text for SRRT.
        text = text.split("Date\nActivity")[1]

        # Because our web rip comes in as a single line of text we need to parse ther string and detect where our newlines should be, then rebuild
        # the text as a list of strings.
        newText = ""
        index = 0

        for char in text:
            try:
                if char.isdigit() and text[index + 1].isdigit() and text[index + 2] == "/" \
                   and text[index + 3].isdigit() and text[index + 4].isdigit() and text[index + 5] == "/" \
                   and text[index + 6].isdigit() and text[index + 7].isdigit() and text[index + 8].isdigit() and text[index + 9].isdigit():

                   newText += "NEWLINE" + char
                else:
                    newText += char
            except IndexError:
                pass # Used to handle a date being entered into a ATR with no other text.
            index += 1

        # Add a new line delimiter.
        newText = newText.split("NEWLINE")
        newText[-1] = newText[-1].split("Next ")[0] # Remove the Next / Previiout records line.

        # Check that the dates meet our date range criteria.
        startDate = win.ui.calStart.selectedDate()
        endDate = win.ui.calEnd.selectedDate()

        for line in newText:
            # Convert the date in our line to a QDate for comparrison
            if line != "\n":
                lineDate =  line[:10].split("/")
                lineDate = QtCore.QDate(int(lineDate[2]), int(lineDate[0]), int(lineDate[1]))

                if lineDate <= endDate:
                    endDateFound = True

                if lineDate < startDate:
                    startDateFound = True
                    break # Stops adding earlier data

            # Add the ATR data if it falls within our date ranges.
            if endDateFound and not startDateFound:
                output.append(line)

        if not endDateFound or not startDateFound:
            webPage += 1

    return output
    #------------------------------------------------------------------------------------------------------------------------------------------------#


def getPilotCredentials():

    rank = 2
    ranks = ["UNUSED", "CT", "SL", "LT", "LCM", "CM", "CPT", "MAJ", "LC", "COL", "GN", "RA", "VA", "AD", "FA", "HA"]
    maxRank = "UNKNOWN"
    position = 4
    # Rank as string, max rank as int
    positions = [["UNUSED", 0], ["TRN", 0], ["FM", 6], ["FL", 8], ["CMDR", 9], ["WC", 9], ["COM", 12], ["COO", 13], ["SOO", 13], ["TCCOM", 14]]

    pilotName = win.ui.cbPilots.currentText()

    # Determine pilot Pin number.
    pin = 0
    for pilot in win.pilots:
        if pilot[1] == pilotName:
            pin = pilot[0]
            break

    url = "https://tc.emperorshammer.org/TTT2backend.php?pin=" + pin
    text = getTextListFromHtml(url).split("\n")

    # Determin if pilot has achieved their max rank.
    if int(text[rank]) >= positions[int(text[position])][1]:
        maxRank = "Y"
    else:
        maxRank = "N"

    # return strRank strPos strMax
    return ranks[int(text[rank])] + "\t", positions[int(text[position])][0] + "\t", maxRank + "\t"
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
    misc = 0
    reviews = 0
    bugReports = 0
    medals = {}
    iwats = 0

    # Strings
    newData = []
    unprocessed = "\n\n-----Lines from Input that SRRT was not able to process:-----\n\n"
    spMissionDict = {}
    spMissiontext = ""
    highscoreText = ""
    fchgText = ""
    combatText = ""
    coopPVEText = ""
    uniformUpdated = False
    uniformText = ""
    reviewsDict = {}
    reviewText = ""
    bugReportsDict = {}
    bugReportText = ""
    promotionText = ""
    assignmentText = ""
    iwatsText = ""
    inprUpdated = False
    inprText = ""
    miscText = ""

    # Retrieve the pilots data for the selected pilot in the Pilots: comboBoz.
    data = getPilotActivityData(win.ui.cbPilots.currentText())

# ----------Parse the data for processing.----------
    for line in data:
        if line != "\n":

            # -----SP Missions-----
            if "Battle completed : " in line and "mission" in line:

                # MSE Score.
                result = line.split("(")[1]
                result = result.split(" ")[0]
                spMissions += int(result)

                # WSR Text.
                    # Extract ther desired text e.g. TIE-TC 34
                result = line.split(" : ")[1]
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
                    sortieLine = sortieLine.split(" : ")[1]
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


            # -----LoCs-----
            elif "of Combat" in line:

                # Single Award:
                if "Legion of Combat (LoC)" in line:
                    locs += 1

                # Multi Award:
                elif "Legions of Combat (LoCs)" in line:
                    result = line.split(":")[1]
                    result = result.split(" ")[1]
                    locs += int(result)

                # Error handling:
                else:
                    newData.append(line)
                    unprocessed += line + "\n"


            # -----LoSs-----
            elif "of Skirmish" in line:

                # Single award
                if "Legion of Skirmish (LoS)" in line:
                    loss += 1

                # Multi award
                elif "Legions of Skirmish (LoSs)" in line:
                    result = line.split(":")[1]
                    result = result.split(" ")[1]
                    loss += int(result)

                # Error handling:
                else:
                    newData.append(line)
                    unprocessed += line + "\n"


            # -----Iron Stars-----
            elif "Iron Star" in line:
                result = line.split(" : ")[1]

                # Platinum
                if "Platinum" in result:
                    if "Ribbon" in result:
                        ISPR += 1
                    elif "Wings" in result:
                        ISPW += 1
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Gold
                elif "Gold" in result:
                    if "Ribbon" in result:
                        ISGR += 1
                    elif "Wings" in result:
                        ISGW += 1
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Silver
                elif "Silver" in result:
                    if "Ribbon" in result:
                        ISSR += 1
                    elif "Wings" in result:
                        ISSW += 1
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Bronze
                elif "Bronze" in result:
                    if "Ribbon" in result:
                        ISBR += 1
                    elif "Wings" in result:
                        ISBW += 1
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"

                # Copper
                elif "Copper" in result:
                    if "Ribbon" in result:
                        ISCR += 1
                    elif "Wings" in result:
                        ISCW += 1
                    else:
                        newData.append(line) # Error handling.
                        unprocessed += line + "\n"


                # Re-add the line if we can't detect the award so this it will be displayed at the bottom of the WSR output.
                else:
                    newData.append(line)
                    unprocessed += line + "\n"


            # ----- Medal of Instruction (MoI)-----
            elif "Medal of Instruction (MoI)" in line:
                mois += 1


            # -----FCHG Rating-----
            elif "Flight Certification Wings awarded" in line:
                result = line.split(" : ")[1]
                fchgText += "\nAchieved Flight Certification Wings rank of %s"%result.replace("\n", "")

            # -----Combat Rating-----
            elif "New Combat Rating achieved : " in line:
                result = line.split(" : ")[1]
                combatText += "\nAchieved Combat Rating of %s"%result.replace("\n", "")


            # -----COOP/PVE Rating-----
            elif "New COOP/PVE Rating achieved : " in line:
                result = line.split(" : ")[1]
                coopPVEText += "\nAchieved COOP/PVE Rating of %s"%result.replace("\n", "")


            # -----Uniform Update-----
            elif "New uniform upload approved" in line:
                if not uniformUpdated:
                    uniformText = "\nUpdated their uniform"
                    misc += 1
                    uniformUpdated = True


            # -----INPR Update-----
            elif "Updated Imperial Navy Personnel Record (INPR)" in line:
                if not inprUpdated:
                    inprText = "\nUpdated their Imperial Navy Personnel Record (INPR)"
                    misc += 1
                    inprUpdated = True


            # -----Mission Bug Reports-----
            elif "Submitted bug report" in line:

                # Patch bug reports
                if "patch" in line:
                    result = line.split("patch ")[1]

                # Normal bug reports.
                else:
                    # Extract ther desired text e.g. TIE-TC 34
                    result = line.split("battle ")[1]

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
            elif "Medal awarded : " in line:
                result = line.split(" : ")[1].replace("\n", "")
                if result not in medals:
                    medals[result] = 1
                else:
                    medals[result] += 1


            # -----Promotions-----
            elif "new rank set " in line.lower() or "new promotion : " in line.lower():
                result = line.split(" : ")[1].replace("\n", "")
                promotionText += "\nPromoted to the rank of %s"%result


            # -----Assignments-----
            elif "New assignment :" in line:
                result = line.split(":")[1].rstrip("Previous Records ")
                assignmentText += "\nAssigned to: " + result.replace("\n", "")


            # -----IWATS Courses.-----
            elif "IWATS Course added to Academic Record" in line:
                results = line.split(" : ")[1].split(" - ")
                iwatsText += "\nCompleted the IWATS/Imp U %s course with a score of %s"%(results[0], results [1].replace("\n", ""))
                iwats += 1
                misc += 1


            # -----Reports-----
            elif "Submitted a new" in line and "report" in line:
                reports += 1
                reportsDatabased += 1


            # Write un proccessed lines back to the New Data.txt file.
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

    rank, pos, maxRank = getPilotCredentials()
    scoreLine = date + rank + pos + squad + moc + maxRank

##    # Convert items that equal '0' to nothing.
##    scoredItems = [spMissions, locs, loss, ISPR + ISPW, ISGR + ISGW + dfc, ISSR + ISSW, ISBR + ISBW, missHScore, battHScore, reports,
##                   reportsDatabased, reportsOC, comps, compsOC,  compsRunDWB, mois, misc]

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
              + highscoreText + reviewText + bugReportText + fchgText + combatText + coopPVEText + iwatsText + uniformText + inprText
    wsrLine = wsrLine.strip("\n") # Removes the leading newline.

    # LoCs
    if locs != 0:
        if locs == 1:
            wsrLine += "\nAwarded %sx Legion of Combat (LoC)"%locs
        else:
            wsrLine += "\nAwarded %sx Legions of Combat (LoCs)"%locs

    # LoSs
    if loss != 0:
        if loss == 1:
            wsrLine += "\nAwarded %sx Legion of Skirmish (LoS)"%loss
        else:
            wsrLine += "\nAwarded %sx Legions of Skirmish (LoSs)"%loss


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
        wsrLine += "\nAwarded %sx Iron Star with Copper Ribbon (IS-BR)"%ISCR

    if ISCW != 0:
        wsrLine += "\nAwarded %sx Iron Star with Copper Wings (IS-BW)"%ISCW


    # ---------- Other Medals ----------
    for medal in medals:
        wsrLine += "\nAwarded %sx %s"%(medals[medal], medal)


    # ----------Misc text.----------
    if reviews != 0:
        miscText += "\n{0}x points for writing {0}x reviews".format(reviews)

    if bugReports != 0:
        miscText += "\n{0}x points for writing {0}x bug reports".format(bugReports)

    if uniformUpdated:
        miscText += "\n1x point for updating their uniform"

    if inprUpdated:
        miscText += "\n1x point for updating their INPR"

    if iwats != 0:
        miscText += "\n{0}x points for completing {0}x IWATS courses".format(iwats)


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
