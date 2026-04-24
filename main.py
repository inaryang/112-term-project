# =========== AI DECLARATION ============

'''
I used Claude to organize my code and create my section labels and some comments.
I also used Claude to find libraries I need and how to navigate these libraries
I used AI generally over the project to help debug, especially with lines of code
where I was not familiar with the libraries or type of object, especially text boxes
AI also wrote some skeletons for functions, and helped me decide what methods I need
Lastly, I used AI to offload some of the busy work like when I wanted to change the colors of
multiple buttons and manually would have to go back and change each line. I could just copy and paste
the changes AI made on all of them at once which took a tenth of the time.
Despite the use of AI, I fully understand my code and can explain what each line does.
'''

# ============ FEATURE STRING ============

# =============== IMPORTS ================

from cmu_graphics import *
import math
import statistics
import yfinance as yf
import random

# ============== CONSTANTS ===============

LEFT_PANEL_WIDTH = 650      # chart area panel on left
RIGHT_PANEL_WIDTH = 325     # panel width on right
RIGHT_PANEL_X = 670         # where right side panels start
RIGHT_PANEL_LABEL_X = RIGHT_PANEL_X + RIGHT_PANEL_WIDTH/2 #center of panel
SLIDER_START_Y = 120        # first slider y position
SLIDER_WIDTH = 250          # slider line length
SLIDER_SPACING = 70         # vertical gap between sliders
SLIDER_HANDLE_RADIUS = 8    #slider circle/handle radius

PLOT_LEFT = 70              #left side of chart
PLOT_RIGHT = 620            #right side of chart
PLOT_TOP = 60               #top of chart
PLOT_BOTTOM = 640           #bottom of chart

POSTIT_FILL = rgb(255, 253, 156)
SCHOOL_FONT = 'xkcd'

NUM_BINS = 100
COVERAGE_THRESHOLD = 0.85

# =========== BLACK-SCHOLES MATH =========

N = statistics.NormalDist().cdf

# S - current price, K - strike price, T - option lifespan remaining
# sigma - volatility, r - risk-free interest rate
# d1,d2 - how likely option is worth using given volatility and time
# N(d1) = P(Z < d1)
def blackScholes(S,K,T,r,sigma):
    d1 = (math.log(S/K) + (r + (sigma**2)/2)*T)/(sigma*math.sqrt(T))
    d2 = d1 - (math.sqrt(T)*sigma)

# ln(S/K) - "how far is stock from strike price rn"
# (r + sigma**2/2)*T - "how much will the stock drift up over time"
# sigma*sqrt(T) - "how much randomness is there over the life of the option"
    call = S * N(d1) - K * math.e**(-r * T) * N(d2)
    put = K * math.e**(-r * T) * N(-d2) - S * N(-d1)
    return call,put

# ============ SLIDER CLASS ==============
class Slider:
    def __init__(self, id, label, x, y, width, minVal, maxVal, currVal):
        self.id = id # 'S','K','T','r','sigma'
        self.label = label #the actual name that shows up
        self.x = x #starting
        self.y = y
        self.width = width
        self.minVal = minVal
        self.maxVal = maxVal
        self.currVal = currVal

    def getSliderX(self):
        proportion = (self.currVal - self.minVal) / (self.maxVal - self.minVal)
        return self.x + proportion * self.width

    def updateValueFromMouse(self, mouseX):
        proportion = (mouseX - self.x) / self.width
        proportion = max(0, min(1, proportion))
        self.currVal = self.minVal + proportion * (self.maxVal - self.minVal)

    def isMouseOver(self, mouseX, mouseY):
        # has a vertical margin it accepts along length of track
        withinX = self.x <= mouseX <= self.x + self.width
        withinY = abs(mouseY - self.y) <= SLIDER_HANDLE_RADIUS + 4
        return withinX and withinY

# ============ TEXT CLASS ==============
class TextInput:
    def __init__(self, id, x, y, width, height, initialValue, allowLetters=False):
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.allowLetters = allowLetters
        self.error = False          # error if not valid ticker
        self.highlighted = False    # price and volatility set to stock

        # initial text: ticker allowed if ticker box, otherwise only numbers
        if allowLetters:
            self.text = str(initialValue)
        else:
            self.text = f"{initialValue:.2f}"
        self.selected = False

    def isMouseOver(self, mouseX, mouseY):
        return (self.x <= mouseX <= self.x + self.width
                and self.y <= mouseY <= self.y + self.height)

    def handleKey(self, key):
        if not self.selected:
            return
        self.error = False
        self.highlighted = False
        if key == 'backspace':
            self.text = self.text[:-1]
        elif len(key) == 1:
            if self.allowLetters and key.isalpha():
                self.text += key.upper()
            elif key.isdigit() or key == '.':
                if key == '.' and '.' in self.text:
                    return
                self.text += key

    def setValueFromNumber(self, value):
        self.text = f"{value:.2f}"

    def getValue(self):
        try:
            return float(self.text)
        except ValueError:
            return None

# ================ MODEL =================

def onAppStart(app):

    # --- Constants ---
    app.width = 1010
    app.height = 700

    # --- Black-Scholes Inputs ---
    app.S = 100
    app.K = 100
    app.T = 1.0
    app.r = 0.05
    app.sigma = 0.2

    # --- Prices + Greeks ---
    app.callPrice = 0
    app.putPrice = 0
    app.delta = 0
    app.gamma = 0
    app.theta = 0
    app.vega = 0

    # --- UI ---
    app.mode = 'start'
    app.currSlider = None
    app.showCall = True

    # --- Sliders ---
    # CLAUDE TOLD ME TO ADD buildSliders / buildTextInputs for readablity
    app.sliders = buildSliders(app)
    app.textInputs = buildTextInputs(app)
    app.selectedInput = None
    app.tickerInput = TextInput("ticker", 490, 15, 80, 22, "AAPL", allowLetters=True)

    # --- Test ---
    app.testPhase = 'selectLevel'
    app.testLevel = None
    app.testShowCall = True
    app.testUserPoints = []
    app.testChartBounds = None
    app.testScore = None
    app.testSubmitMessage = None
    app.testSliderLock = False
    app.testDrawing = False  # True while mouse held down in chart section
    app.testAvgError = None

    recomputePrices(app)

def buildSliders(app):
    x = RIGHT_PANEL_X+40
    y = SLIDER_START_Y
    return [
        Slider("S", "S (Current Stock Price)", x, y,                     SLIDER_WIDTH, 1,    1000, app.S),
        Slider("K", "K (Strike Price)",        x, y + SLIDER_SPACING,    SLIDER_WIDTH, 1,    1000, app.K),
        Slider("T", "T (Time, years)",         x, y + SLIDER_SPACING*2,  SLIDER_WIDTH, 1/12,        5.0,  app.T),
        Slider("r", "r (Risk-Free Rate)",      x, y + SLIDER_SPACING*3,  SLIDER_WIDTH, 0.0,  0.20, app.r),
        Slider("σ", "sigma (Volatility)",      x, y + SLIDER_SPACING*4,  SLIDER_WIDTH, 0.015, 1.00, app.sigma),
    ]
def recomputePrices(app):
    for slider in app.sliders:
        if slider.id == "S":
            app.S = slider.currVal
        elif slider.id == "K":
            app.K = slider.currVal
        elif slider.id == "T":
            app.T = slider.currVal
        elif slider.id == "r":
            app.r = slider.currVal
        elif slider.id == "σ":
            app.sigma = slider.currVal
    app.callPrice, app.putPrice = blackScholes(app.S,app.K,app.T,app.r,app.sigma)
    computeGreeks(app)

def buildTextInputs(app):
    TEXT_BOX_WIDTH = 70
    TEXT_BOX_HEIGHT = 22
    result = []
    for slider in app.sliders:
        # position: same row as label above slider
        tx = slider.x + slider.width - TEXT_BOX_WIDTH
        ty = slider.y - 30 - TEXT_BOX_HEIGHT/2   # y of TOP of text box
        result.append(TextInput(slider.id, tx, ty, TEXT_BOX_WIDTH, TEXT_BOX_HEIGHT, slider.currVal))
    return result

def computeGreeks(app):
    h = 0.01 # small enough to be a good derivative, big enough to avoid float issues, works as the derivative

    S, K, T, r, sigma = app.S, app.K, app.T, app.r, app.sigma

    # Pick call or put based on showCall
    def price(S_, K_, T_, r_, sigma_):
        call, put = blackScholes(S_, K_, T_, r_, sigma_)
        return call if app.showCall else put

    #Delta: dV/dS
    priceHigh = price(S + h, K, T, r, sigma)
    priceLow = price(S - h, K, T, r, sigma)
    delta = (priceHigh - priceLow) / (2 * h)

    # Gamma: d2V/dS2
    priceHigh = price(S + h, K, T, r, sigma)
    priceMid = price(S, K, T, r, sigma)  # <-- this is just the current price
    priceLow = price(S - h, K, T, r, sigma)
    gamma = (priceHigh - 2 * priceMid + priceLow) / (h ** 2)

    # Vega: dV/dsigma
    priceHigh = price(S, K, T, r, sigma + h)
    priceLow = price(S, K, T, r, sigma - h)
    vega = (priceHigh - priceLow) / (2 * h)
    vega *= 0.01  # convert from "per 1.0 change in sigma" to "per 1% change"

    # Theta: dV/dT(365) for per day
    priceHigh = price(S, K, T + h, r, sigma)
    priceLow = price(S, K, T - h, r, sigma)
    theta = -(priceHigh - priceLow) / (2 * h)  # negative because time flows forward = value decays
    theta /= 365  # per-day (calendar) rather than per-year

    app.delta = delta
    app.gamma = gamma
    app.vega = vega
    app.theta = theta

def buildTestProblems(app):
    # (how many sliders move, True if only endpoints)

    LEVEL_RULES = {
        1: (1,True),
        2: (2,True),
        3: (2,False),
        4: (3,False),
        5: (4,False)
    }
    app.testDrawing = False
    moveCount, endpointsOnly = LEVEL_RULES[app.testLevel]

    # reset to midpoint
    for slider in app.sliders:
        slider.currVal = (slider.minVal + slider.maxVal) / 2

    movingSliders = random.sample(app.sliders,moveCount)

    for movingSlider in movingSliders:
        if endpointsOnly:
            movingSlider.currVal = random.choice([movingSlider.minVal, movingSlider.maxVal])
        else:
            movingSlider.currVal = random.uniform(movingSlider.minVal, movingSlider.maxVal)

    recomputePrices(app)

    #sync textboxes
    for slider in app.sliders:
        syncTextInputFromSlider(app, slider)

    # freeze chart bounds since they aren't moving
    minX = min(app.S, app.K) * 0.5
    maxX = max(app.S, app.K) * 1.5
    minY = 0

    # maxY same as drawChart
    samples, maxBS = sampleBSCurve(app, minX, maxX, app.testShowCall)
    if app.testShowCall:
        maxY = max(maxX - app.K, maxBS) * 1.1
    else:
        maxY = max(app.K - minX, maxBS) * 1.1
    app.testChartBounds = (minX, maxX, minY, maxY)

    # clear last round
    app.testUserPoints = []
    app.testScore = None
    app.testSubmitMessage = None

def inChartArea(mouseX,mouseY):
    return (PLOT_LEFT <= mouseX <= PLOT_RIGHT and
            PLOT_TOP <= mouseY <= PLOT_BOTTOM)

'''
AI USE: CLAUDE
PROBLEM: program wouldn't register if user drawing was below the curve
SOLUTION: track coverage using x-coordinate bins regardless of y
WHERE: computeCoverage
'''
def computeCoverage(app):
    if (not app.testUserPoints) or (app.testChartBounds is None):
        return 0.0
    minX, maxX, minY, maxY = app.testChartBounds
    binWidth = (maxX - minX) / NUM_BINS
    binsTouched = set()

    # mark each individual point's bin
    for (dx, dy) in app.testUserPoints:
        binIdx = int((dx - minX) / binWidth)
        if 0 <= binIdx < NUM_BINS:
            binsTouched.add(binIdx)

    # fill in bins between consecutive points
    for i in range(1, len(app.testUserPoints)):
        x1 = app.testUserPoints[i-1][0]
        x2 = app.testUserPoints[i][0]
        binA = int((min(x1, x2) - minX) / binWidth)
        binB = int((max(x1, x2) - minX) / binWidth)
        for b in range(binA, binB + 1):
            if 0 <= b < NUM_BINS:
                binsTouched.add(b)

    return len(binsTouched) / NUM_BINS

def gradeTestDrawing(app):
    # bin user's drawing by (x, average y) in each bin.
    # for each bin the user covered, compare to true BS y at bin center.
    # accuracy = max(0.0, 100 * (1 - normalizedError / TOLERANCE))
    if not app.testUserPoints or app.testChartBounds is None:
        return None

    minX, maxX, minY, maxY = app.testChartBounds
    binWidth = (maxX - minX) / NUM_BINS

    # collect y-values in each bin
    binYValues = {}   # binIdx -> list of y values
    for (dx, dy) in app.testUserPoints:
        binIdx = int((dx - minX) / binWidth)
        if 0 <= binIdx < NUM_BINS:
            if binIdx not in binYValues:
                binYValues[binIdx] = []
            binYValues[binIdx].append(dy)

    # average each bin, compare to true BS at bin center
    totalAbsError = 0
    numBinsScored = 0
    for binIdx, yList in binYValues.items():
        userAvgY = sum(yList) / len(yList)
        binCenterX = minX + (binIdx + 0.5) * binWidth
        call, put = blackScholes(binCenterX, app.K, app.T, app.r, app.sigma)
        trueY = call if app.testShowCall else put
        totalAbsError += abs(userAvgY - trueY)
        numBinsScored += 1

    if numBinsScored == 0:
        return None

    avgError = totalAbsError / numBinsScored
    yRange = maxY - minY
    normalizedError = avgError / yRange if yRange > 0 else 0

    TOLERANCE = 0.25   # 25% of chart height avg error = 0 points
    score = max(0, 100 * (1 - normalizedError / TOLERANCE))

    return (score, avgError)

def fetchHistoricalPrices(ticker, period):
    # returns list of daily closing prices or None if it fails
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if len(hist) == 0:
            return None
        return hist['Close'].tolist()
    except Exception:
        return None

def computeHistoricalVolatility(prices):
    if len(prices) < 2:
        return None
    logReturns = []
    for i in range(1, len(prices)):
        logReturns.append(math.log(prices[i] / prices[i-1]))
    dailyVol = statistics.stdev(logReturns)
    return dailyVol * math.sqrt(252)

def loadTickerData(app, ticker):
    # gets real market data for ticker and updates app stat
    # returns True unless it fails then False

    prices = fetchHistoricalPrices(ticker, "3mo")
    if prices is None or len(prices) < 2:
        return False

    currentPrice = prices[-1]
    vol = computeHistoricalVolatility(prices)
    if vol is None:
        return False

    # clamp to slider ranges so they don't go out of bounds and cause errors
    sliderS = findSliderById(app, "S")
    sliderSigma = findSliderById(app, "σ")

    newS = max(sliderS.minVal, min(sliderS.maxVal, currentPrice))
    newSigma = max(sliderSigma.minVal, min(sliderSigma.maxVal, vol))

    sliderS.currVal = newS
    sliderSigma.currVal = newSigma

    # sync text inputs w/ data
    syncTextInputFromSlider(app, sliderS)
    syncTextInputFromSlider(app, sliderSigma)

    # update app
    recomputePrices(app)

    # highlight s and sigma boxes to show it's the original stock data
    for textInput in app.textInputs:
        if textInput.id in ("S", "σ"):
            textInput.highlighted = True

    return True

def handleTickerLoad(app):
    ticker = app.tickerInput.text.strip().upper()
    if ticker == "":
        app.tickerInput.error = True
        return
    success = loadTickerData(app, ticker)
    if success:
        app.tickerInput.error = False
    else:
        app.tickerInput.error = True

# ================ VIEW ==================
'''
Note: black-scholes is european options so the BS price can dip below the payoff  
when the put is deep in-the-money and T is big. reflects opportunity cost of waiting which is real 
in european options and is not a bug
'''
def dataToScreen(dataX,dataY,minX,maxX,minY,maxY):
    screenX = PLOT_LEFT + (dataX-minX)/(maxX-minX) * (PLOT_RIGHT-PLOT_LEFT)
    screenY = PLOT_BOTTOM - (dataY - minY) / (maxY - minY) * (PLOT_BOTTOM - PLOT_TOP)
    return (screenX, screenY)

def screenToData(screenX, screenY, minX, maxX, minY, maxY):
    dataX = minX + (screenX - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT) * (maxX - minX)
    dataY = minY + (PLOT_BOTTOM - screenY) / (PLOT_BOTTOM - PLOT_TOP) * (maxY - minY)
    return (dataX, dataY)

def commitTextInput(app, textInput):
    matching = findSliderById(app, textInput.id)
    if matching is None:
        return  # no matching slider so do nothing

    value = textInput.getValue()
    if value is None:
        textInput.setValueFromNumber(matching.currVal)
        return

    value = max(matching.minVal, min(matching.maxVal, value)) #clamp
    matching.currVal = value
    textInput.setValueFromNumber(value)
    recomputePrices(app)

def findSliderById(app, id):
    for slider in app.sliders:
        if slider.id == id:
            return slider
    return None

def syncTextInputFromSlider(app, slider):
    for textInput in app.textInputs:
        if textInput.id == slider.id:
            textInput.setValueFromNumber(slider.currVal)
            textInput.highlighted = False
            return

def switchTestOptionType(app, showCall):
    # User toggled call/put mid-round. Keep the slider values, but
    # regenerate chart bounds and payoff for the new option type,
    # and clear their drawing.
    app.testShowCall = showCall

    minX, maxX, minY, maxY_old = app.testChartBounds
    # recompute maxY for the new option type
    samples, maxBS = sampleBSCurve(app, minX, maxX, app.testShowCall)
    if app.testShowCall:
        maxY = max(maxX - app.K, maxBS) * 1.1
    else:
        maxY = max(app.K - minX, maxBS) * 1.1
    app.testChartBounds = (minX, maxX, 0, maxY)

    # clear drawing — user is solving a different problem now
    app.testUserPoints = []
    app.testDrawing = False

def redrawAll(app):
    drawBackground(app)

    if app.mode == "start":
        drawIntroScreen(app)

    elif app.mode == "main":
        drawSliderPanel(app)
        drawPricePanel(app)
        drawGreekPanel(app)
        drawChart(app)
        drawTickerBar(app)

    elif app.mode == 'test':
        drawTestScreen(app)

    elif app.mode == 'instructions':
        drawInstructionsScreen(app)

    elif app.mode == 'explanation':
        drawExplanationScreen(app)

def drawSliderPanel(app):
    drawRect(RIGHT_PANEL_X, 50, app.width - RIGHT_PANEL_X - 15, 380,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLabel("SLIDERS", RIGHT_PANEL_LABEL_X, 30, size=20, bold=True,font=SCHOOL_FONT)



    for i, slider in enumerate(app.sliders):
        x = slider.getSliderX()
        drawLabel(slider.label, slider.x, slider.y - 30, align='left')
        drawLine(slider.x, slider.y, slider.x + slider.width, slider.y)
        drawCircle(x, slider.y, SLIDER_HANDLE_RADIUS, fill='black')
        drawLabel(slider.id, x, slider.y, size=10, fill='white', bold=True)

        # matching text input
        drawTextInput(app.textInputs[i])


def drawTextInput(textInput):
    if textInput.error:
        borderColor = 'red'
        fillColor = rgb(255, 240, 240)
    elif textInput.selected:
        borderColor = 'blue'
        fillColor = 'white'
    elif textInput.highlighted:
        borderColor = rgb(50, 180, 100)  # green accent to show original stock data
        fillColor = rgb(240, 255, 245)
    else:
        borderColor = 'gray'
        fillColor = rgb(245, 245, 245)

    drawRect(textInput.x, textInput.y, textInput.width, textInput.height,
             fill=fillColor, border=borderColor, borderWidth=1)
    drawLabel(textInput.text,
              textInput.x + textInput.width / 2,
              textInput.y + textInput.height / 2,
              size=11,font=SCHOOL_FONT)

def drawPricePanel(app):

    drawRect(RIGHT_PANEL_X, 475, app.width - RIGHT_PANEL_X - 20, 70, fill=POSTIT_FILL,
             border='black', borderWidth=3,opacity=60)
    drawLine(RIGHT_PANEL_LABEL_X, 475, RIGHT_PANEL_LABEL_X, 545)
    drawLabel("PRICES", RIGHT_PANEL_LABEL_X, 455, size=20, bold=True,font=SCHOOL_FONT)
    drawLabel("CALL", RIGHT_PANEL_X+RIGHT_PANEL_WIDTH/4, 495, size=16, bold=True,font=SCHOOL_FONT)
    drawLabel("PUT", RIGHT_PANEL_X+RIGHT_PANEL_WIDTH*0.75, 495, size=16, bold=True,font=SCHOOL_FONT)
    drawLabel(f'${app.callPrice:.2f}', RIGHT_PANEL_X+RIGHT_PANEL_WIDTH/4, 520, size=16)
    drawLabel(f'${app.putPrice:.2f}', RIGHT_PANEL_X+RIGHT_PANEL_WIDTH*0.75, 520, size=16)


def drawGreekPanel(app):
    drawRect(RIGHT_PANEL_X, 595, app.width - RIGHT_PANEL_X - 15, 80,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLabel("GREEKS", RIGHT_PANEL_LABEL_X, 575, size=20, bold=True,font=SCHOOL_FONT)

    drawLine(RIGHT_PANEL_X, 635, RIGHT_PANEL_X+RIGHT_PANEL_WIDTH, 635) #horizontal line

    # 3 vertical lines
    step = RIGHT_PANEL_WIDTH / 4
    for i in range(1, 4):
        drawLine(RIGHT_PANEL_X + step * i, 595, RIGHT_PANEL_X + step * i, 675)
    '''
    AI USE: CLAUDE
    PROBLEM: original code was opposite of beautiful but worked
    SOLUTION: enumerate(index,item) counts index and item at same time
    WHERE: here to the end of drawGreekPanel
    '''

    # greeks: (symbol, value, format string)
    greeks = [
        ("Δ", app.delta, ".3f"),  # delta around 0.01 to 1.00
        ("Γ", app.gamma, ".4f"),  # gamma very small, needs 4 decimals
        ("Θ", app.theta, ".4f"),  # theta also very small
        ("ν", app.vega, ".3f"),  # vega around 0.1 to 0.5 range (lowercase nu, not v)
    ]

    for i, (symbol, value, fmt) in enumerate(greeks):
        cx = RIGHT_PANEL_X + step/2 + step * i  # column center x
        drawLabel(symbol, cx, 615, size=16, bold=True)
        drawLabel(f'{value:{fmt}}', cx, 655, size=14)

def drawChart(app):
    drawBackButton()
    minX = min(app.S, app.K) * 0.5
    maxX = max(app.S, app.K) * 1.5
    minY = 0

    samples, maxBS = sampleBSCurve(app, minX, maxX)

    if app.showCall:
        maxY = max(maxX - app.K, maxBS) * 1.1
    else:
        maxY = max(app.K - minX, maxBS) * 1.1

    def toScreen(dx, dy):
        return dataToScreen(dx, dy, minX, maxX, minY, maxY)

    drawChartPanelAxes()  # panel + axes
    drawChartTicks(toScreen, minX, maxX, minY, maxY)  # tick marks
    drawChartTitleLegend(app)  # title + legend
    drawSMarker(app, toScreen, maxY)  # S-line + label
    drawPayoff(app, toScreen, minX, maxX)  # blue hockey stick
    drawBSCurve(toScreen, samples)  # green curve

def drawChartPanelAxes():
    drawRect(PLOT_LEFT - 45, PLOT_TOP - 15, PLOT_RIGHT - PLOT_LEFT + 60,
             PLOT_BOTTOM - PLOT_TOP + 50,fill=rgb(250, 250, 252),
             border=rgb(180, 180, 190), borderWidth=3)
    drawLine(PLOT_LEFT,PLOT_BOTTOM,PLOT_RIGHT,PLOT_BOTTOM)
    drawLine(PLOT_LEFT,PLOT_TOP,PLOT_LEFT,PLOT_BOTTOM)

def drawChartTicks(toScreen, minX, maxX, minY, maxY):
    # x-axis ticks
    NUM_X_TICKS = 6
    for i in range(NUM_X_TICKS + 1):
        # data value at this tick
        value = minX + i * (maxX - minX) / NUM_X_TICKS
        # screen position on x-axis
        screenX, _ = toScreen(value, 0)
        # short tick line sticking down from the axis
        drawLine(screenX, PLOT_BOTTOM, screenX, PLOT_BOTTOM + 5)
        # number label below tick
        drawLabel(f'${value:.0f}', screenX, PLOT_BOTTOM + 15, size=9)

    # y-axis ticks
    NUM_Y_TICKS = 5
    for i in range(NUM_Y_TICKS + 1):
        value = minY + i * (maxY - minY) / NUM_Y_TICKS
        _, screenY = toScreen(minX, value)
        drawLine(PLOT_LEFT - 5, screenY, PLOT_LEFT, screenY)
        drawLabel(f'${value:.0f}', PLOT_LEFT - 12, screenY, size=9, align='right')

def drawChartTitleLegend(app):
    optionType = "CALL" if app.showCall else "PUT"
    drawLabel(f"{optionType} OPTION VALUE VS STOCK PRICE", 130,
              PLOT_TOP - 37, size=16, bold=True, align='left',font=SCHOOL_FONT)

    # legend in top-right of chart
    LEGEND_X = PLOT_RIGHT - 150
    LEGEND_Y = PLOT_TOP + 15

    # blue "payoff" curve
    drawLine(LEGEND_X, LEGEND_Y, LEGEND_X + 25, LEGEND_Y, fill='blue', lineWidth=2)
    drawLabel("Payoff", LEGEND_X + 30, LEGEND_Y, size=11, align='left')

    # green "BS price" curve
    drawLine(LEGEND_X, LEGEND_Y + 20, LEGEND_X + 25, LEGEND_Y + 20, fill='green', lineWidth=2)
    drawLabel("Black-Scholes Price", LEGEND_X + 30, LEGEND_Y + 20, size=11, align='left')

    # tape
    drawRect(615,226,40,100,opacity=20)
    drawRect(615, 480, 40, 100,opacity=20)
    drawRect(5, 226, 40, 100, opacity=20)
    drawRect(5, 480, 40, 100, opacity=20)

    '''
    AI USE: CLAUDE
    PROBLEM: curve extending past top of plot when T was high
    SOLUTION: reordered my code to make a sample of curve first then convert to screen position
    WHERE: sampleBSCurve, drawPayoff, drawBSCurve
    '''

def drawSMarker(app, toScreen, maxY):
    topX, topY = toScreen(app.S, maxY)
    botX, botY = toScreen(app.S, 0)
    drawLine(topX, topY, botX, botY, fill='red', opacity=40, dashes=True)
    drawLabel(f'S = {app.S:.2f}', topX, PLOT_TOP - 5, size=10, fill='red', border='black', borderWidth=0.4)

def drawPayoff(app, toScreen, minX, maxX, showCall=None):
    if showCall is None:
        showCall = app.showCall
    if showCall:
        x1, y1 = toScreen(minX, 0)
        x2, y2 = toScreen(app.K, 0)
        x3, y3 = toScreen(maxX, maxX - app.K)
        drawLine(x1, y1, x2, y2, fill='blue', lineWidth=2)
        drawLine(x2, y2, x3, y3, fill='blue', lineWidth=2)
    else:
        x1, y1 = toScreen(minX, app.K - minX)
        x2, y2 = toScreen(app.K, 0)
        x3, y3 = toScreen(maxX, 0)
        drawLine(x1, y1, x2, y2, fill='blue', lineWidth=2)
        drawLine(x2, y2, x3, y3, fill='blue', lineWidth=2)

def drawBSCurve(toScreen, samples):
    prevX = prevY = None
    for sampleS, price in samples:
        sx, sy = toScreen(sampleS, price)
        if prevX is not None:
            drawLine(prevX, prevY, sx, sy, fill='green', lineWidth=2)
        prevX, prevY = sx, sy

def sampleBSCurve(app, minX, maxX, showCall=None):
    if showCall is None:
        showCall = app.showCall
    N_SAMPLES = 100
    samples = []
    maxBS = 0
    for i in range(N_SAMPLES + 1):
        sampleS = minX + i * (maxX - minX) / N_SAMPLES
        call, put = blackScholes(sampleS, app.K, app.T, app.r, app.sigma)
        price = call if showCall else put
        samples.append((sampleS, price))
        if price > maxBS:
            maxBS = price
    return samples, maxBS

def drawTickerBar(app):
    drawLabel("TICKER:", 480, 26, size=13, bold=True, align='right',font=SCHOOL_FONT)
    drawTextInput(app.tickerInput)

    # LOAD button
    drawRect(575, 15, 60, 22, fill=rgb(220, 220, 240), border='black',)
    drawLabel("LOAD", 605, 26, size=12, bold=True,font=SCHOOL_FONT)

def drawBackground(app):
    drawRect(0, 0, app.width, app.height, fill='lightBlue', opacity=30)
    drawLine(100, 0, 100, app.height, fill='red', opacity=40)
    for i in range(1, 25):
        drawLine(0, i * (app.height / 20), app.width, i * (app.height / 20),
                 fill='gray', lineWidth=2, opacity=30)
        if i%3 == 0:
            drawCircle(30, i * (app.height / 20) - app.height / 20, 12, fill='white', border='black')

def drawIntroScreen(app):
    # main labels
    drawLabel("LEARN THE BLACK-SCHOLES MODEL", app.width/2, 55, size=25, bold=True,font=SCHOOL_FONT)
    drawLabel("An interactive learning tool to simplify the complex ideas of options.",
              app.width/2,130,size=20,bold=True,font=SCHOOL_FONT)

    # buttons (rect order is same as label order)
    drawRect(150,200,300,100,fill=POSTIT_FILL,opacity=60,border='black')
    drawRect(550, 200, 300, 100, fill=POSTIT_FILL,opacity=60,border='black')
    drawRect(150,400,300,100,fill=POSTIT_FILL,opacity=60,border='black')
    drawRect(550,400, 300, 100, fill=POSTIT_FILL,opacity=60,border='black')

    drawLabel("INSTRUCTIONS", 300, 250, size=20, bold=True,font=SCHOOL_FONT)
    drawLabel("EXTRA INFO", 700, 250, size=20, bold=True,font=SCHOOL_FONT)
    drawLabel("PRACTICE MODE", 300, 450, size=20, bold=True,font=SCHOOL_FONT)
    drawLabel("TEST MODE", 700, 450, size=20, bold=True,font=SCHOOL_FONT)

'''
AI USE: CLAUDE
PROBLEM: UI FORMATTING
SOLUTION: AI MADE ME A TEMPLATE THAT I COULD TWEAK, OFFLOADED BUSY WORK
WHERE: drawInstructionsScreen, drawExplanationScreen
'''
def drawInstructionsScreen(app):
    drawLabel("INSTRUCTIONS", app.width/2, 50, size=25, bold=True,font=SCHOOL_FONT)
    drawBackButton()

    # ---------- Key functions ----------
    drawLabel("KEY FUNCTIONS", 305, 120, size=20, bold=True,font=SCHOOL_FONT)

    drawRect(120, 140, 370, 500,
             fill=POSTIT_FILL, border='black', borderWidth=3, opacity=60)

    drawLabel("FOR LEARNING/PRACTICE: ", 305, 165, size=14, bold=True,font=SCHOOL_FONT)
    drawLabel("C --> Switch to call option", 305, 200, size=14)
    drawLabel("P --> Switch to put option", 305, 235, size=14)
    drawLabel("ENTER --> Confirm text input", 305, 270, size=14)
    drawLabel("ESC --> Cancel text input", 305, 305, size=14)

    drawLabel("FOR TESTING: ", 305, 375, size=14, bold=True,font=SCHOOL_FONT)
    drawLabel("ENTER --> Submit drawing", 305, 410, size=14)
    drawLabel("C --> Switch to call option test", 305, 445, size=14)
    drawLabel("P --> Switch to put option test", 305, 480, size=14)

    # ---------- How to use ----------
    drawLabel("HOW TO USE THE APP", 755, 120, size=20, bold=True,font=SCHOOL_FONT)

    drawRect(520, 140, 470, 500,
             fill=POSTIT_FILL, border='black', borderWidth=3, opacity=60)

    drawLabel("FOR LEARNING/PRACTICE: ", 755, 165, size=14, bold=True,font=SCHOOL_FONT)
    drawLabel("Drag sliders to change inputs OR click a text box and type a value", 755, 200, size=14)
    drawLabel("Type a ticker (e.g. AAPL) and press LOAD or hit ENTER", 755, 235, size=14)
    drawLabel("to auto-fill real stock price and volatility", 755, 270, size=14)
    drawLabel("Watch the curves move as you change the variables", 755, 305, size=14)

    drawLabel("FOR TESTING: ", 755, 375, size=14, bold=True,font=SCHOOL_FONT)
    drawLabel("You will be shown the positions and values of the sliders", 755, 410, size=14)
    drawLabel("You must draw a curve as close to the true curve as possible", 755, 445, size=14)
    drawLabel("Submit! If your drawing is too small, the submission will be invalid.", 755, 480, size=14)
    drawLabel("PRO TIP: Practice with the learning tool to do better on the tests!", 755, 515, size=14)
    drawLabel("Hit the red BACK button at any time to return to the main screen", 755, 550, size=14)

    drawLabel("GOOD LUCK :-)", 755, 620, size=14, bold=True,font=SCHOOL_FONT)

def drawExplanationScreen(app):
    drawLabel("WHAT DOES THIS APP DO?", app.width/2, 40, size=25, bold=True,font=SCHOOL_FONT)
    drawBackButton()

    PANEL_X = 100

    # ---------- What is an option? ----------
    drawLabel("WHAT IS AN OPTION?", PANEL_X+275, 120,
              size=20, bold=True,align='center',font=SCHOOL_FONT)
    drawRect(PANEL_X, 145, 550, 115,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLabel("An option is a contract to buy (CALL) or sell (PUT) a stock at a set",
              PANEL_X+275, 175, size=14,align='center')
    drawLabel("STRIKE PRICE before it expires. This app uses the Black-Scholes",
              275+PANEL_X, 205, size=14, align='center')
    drawLabel("model to estimate how much that contract is worth today.",
              275+PANEL_X, 235, size=14,align='center')

    # ---------- The greeks ----------
    drawLabel("THE GREEKS", PANEL_X + 275,315, size=20, bold=True,font=SCHOOL_FONT)
    drawRect(PANEL_X, 340, 550, 120,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)

    greekRows = [
        ("Δ  Delta", "If the stock goes up by $1, how much does my option price change?"),
        ("Γ  Gamma", "How fast is Delta itself changing? (the curvature of the curve)"),
        ("Θ  Theta", "If a day passes, how much does my option price decay?"),
        ("ν  Vega",  "If volatility rises 1%, how much does my option price change?"),
    ]
    SYMBOL_X = 110   # symbols align=left
    DESC_X   = SYMBOL_X + 90   # descriptions align=left
    for i, (symbol, desc) in enumerate(greekRows):
        y = 360 + i * 26
        drawLabel(symbol, SYMBOL_X, y, size=15, bold=True, align='left')
        drawLabel("→  " + desc, DESC_X, y, size=13, align='left')

    # ---------- The chart ----------
    drawLabel("THE CHART",  PANEL_X + 275,510, size=20, bold=True,font=SCHOOL_FONT)
    drawRect(PANEL_X, 535, 550, 115,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLabel("Blue line — the PAYOFF at expiration (what you'd get if you exercised now).",
              275+PANEL_X, 560, size=13)
    drawLabel("Green curve — the Black-Scholes PRICE today, usually above the payoff",
              275+PANEL_X, 583, size=13)
    drawLabel("because time and volatility still create upside.",
              275+PANEL_X, 605, size=13)
    drawLabel("Red dashed line — your current stock price S.",
              275+PANEL_X, 627, size=13)

    # ---------- black-scholes ----------
    drawLabel("BLACK-SCHOLES", 805, 90, size=20, bold=True, align='center',font=SCHOOL_FONT)
    drawRect(680,115, 250, 375,
             fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLine(680, 290, 930, 290, fill='black', lineWidth=3,opacity=60)
    drawLabel("C(S,t) = N(d1)S - N(d2)Ke^(-rT)",
              805, 145, size=14, align='center')
    drawLabel("P(S,t) = N(-d2)Ke^(-rT) - N(-d1)S",
              805, 175, size=14, align='center')
    drawLabel("d1 = ",690,217.5,size=14,align='left')
    drawLabel("(ln(S/K) + (r + (sigma^2)/2)*T)",
              915, 205, size=14,align='right')
    drawLine(720,218,920,218,lineWidth=0.7)
    drawLabel("sigma(sqrt(T))",823,230,size=14,align='center')
    drawLabel("d2 = d1 - sigma(sqrt(T))",805,260,size=14)

    drawLabel("C(S,t) -> call option price",805, 310, size=14)
    drawLabel("P(S,t) -> put option price", 805, 340, size=14)
    drawLabel("T -> time left before expiry in years", 805, 370, size=14)
    drawLabel("S -> stock price", 805, 400, size=14)
    drawLabel("r -> risk-free rate", 805, 430, size=14)
    drawLabel("sigma (σ) -> volatility", 805, 460, size=14)

    # ---------- note ----------
    drawRect(680,510,250,160,fill=POSTIT_FILL, border='black', borderWidth=3,opacity=60)
    drawLabel("NOTE!!!",960, 590, size=20,font=SCHOOL_FONT,rotateAngle=90)
    drawLabel("BS Model is designed to", 805, 530, size=14)
    drawLabel("price European options,", 805, 550, size=14)
    drawLabel("which can only be exercised", 805, 570, size=14)
    drawLabel("on the expiration date.", 805, 590, size=14)
    drawLabel("American options have an", 805, 610, size=14)
    drawLabel("early exercise feature that", 805, 630, size=14)
    drawLabel("is unattended with this model", 805, 650, size=14)

def drawTestScreen(app):
    drawBackButton()
    drawSliderPanel(app)

    if app.testPhase == 'selectLevel':
        drawLevelSelection(app)
    elif app.testPhase == 'drawing':
        drawTestDrawingUI(app)
    elif app.testPhase == 'grading':
        drawTestGradedUI(app)

def drawLevelSelection(app):
    drawRect(100, 90, 450, 450,
             fill=POSTIT_FILL, border='black', borderWidth=3, opacity=90)
    drawRect(325,90,100,40,opacity=20,align='center')
    drawLabel("LEVEL SELECTION",325,150,bold=True,size=24,font=SCHOOL_FONT)
    for i in range(1,6):
        drawRect(190,140+i*60,90,30,fill='pink',opacity=90,align='center')
        drawLabel(f"LEVEL {i}: ",150,140 + i*60, font=SCHOOL_FONT,
                  size=20,align='left')
    drawLabel("1 slider changed to an endpoint",250,200,
              size=16,font=SCHOOL_FONT,align='left',bold=True)
    drawLabel("2 sliders changed to an endpoint", 250, 260,
              size=16, font=SCHOOL_FONT, align='left', bold=True)
    drawLabel("2 sliders changed", 250, 320,
              size=16, font=SCHOOL_FONT, align='left', bold=True)
    drawLabel("3 sliders changed", 250, 380,
              size=16, font=SCHOOL_FONT, align='left', bold=True)
    drawLabel("4 sliders changed", 250, 440,
              size=16, font=SCHOOL_FONT, align='left', bold=True)
    drawLabel("Click a highlighted box to select!",325,500,
              size=16, font=SCHOOL_FONT, bold=True)

def drawTestDrawingUI(app):
    minX, maxX, minY, maxY = app.testChartBounds

    def toScreen(dx, dy):
        return dataToScreen(dx, dy, minX, maxX, minY, maxY)

    drawChartPanelAxes()
    drawChartTicks(toScreen, minX, maxX, minY, maxY)
    drawTestChartTitle(app)
    drawSMarker(app, toScreen, maxY)
    drawPayoff(app, toScreen, minX, maxX, app.testShowCall)
    drawUserStroke(app)

    drawStatsPanel(app)
    drawRect(615,226,40,100,opacity=20)
    drawRect(615, 480, 40, 100,opacity=20)
    drawRect(5, 226, 40, 100, opacity=20)
    drawRect(5, 480, 40, 100, opacity=20)

def drawTestChartTitle(app):
    optionType = "CALL" if app.testShowCall else "PUT"
    drawLabel(f"TEST YOURSELF! ({optionType})", 130, 25,
              size=25, bold=True, font=SCHOOL_FONT, align='left')

def drawUserStroke(app):
    if len(app.testUserPoints) < 2:
        return

    minX, maxX, minY, maxY = app.testChartBounds

    def toScreen(dx, dy):
        return dataToScreen(dx, dy, minX, maxX, minY, maxY)

    prevScreenX = prevScreenY = None
    for (dx, dy) in app.testUserPoints:
        sx, sy = toScreen(dx, dy)
        if prevScreenX is not None:
            drawLine(prevScreenX, prevScreenY, sx, sy,
                     fill='green', lineWidth=2)
        prevScreenX, prevScreenY = sx, sy

def drawTestGradedUI(app):
    minX, maxX, minY, maxY = app.testChartBounds

    def toScreen(dx, dy):
        return dataToScreen(dx, dy, minX, maxX, minY, maxY)

    drawChartPanelAxes()
    drawChartTicks(toScreen, minX, maxX, minY, maxY)
    drawTestChartTitle(app)
    drawSMarker(app, toScreen, maxY)
    drawPayoff(app, toScreen, minX, maxX, app.testShowCall)
    drawUserStroke(app)

    # reveal true BS curve in orange
    samples, _ = sampleBSCurve(app, minX, maxX, app.testShowCall)
    prevX = prevY = None
    for (sampleS, price) in samples:
        sx, sy = toScreen(sampleS, price)
        if prevX is not None:
            drawLine(prevX, prevY, sx, sy, fill='orange', lineWidth=3)
        prevX, prevY = sx, sy

    drawStatsPanel(app)   # same panel, phase-aware

def drawStatsPanel(app):
    drawLabel("TEST STATS",
              RIGHT_PANEL_LABEL_X, 455, size=20, bold=True, font=SCHOOL_FONT)
    drawRect(RIGHT_PANEL_X, 480, app.width - RIGHT_PANEL_X - 15, 195,
             fill=POSTIT_FILL, border='black', borderWidth=3, opacity=60)

    drawLabel(f"LEVEL: {app.testLevel}",
              RIGHT_PANEL_LABEL_X, 510, font=SCHOOL_FONT, size=18)

    if app.testPhase == 'grading':
        # --- Show results ---
        score = app.testScore
        if score >= 85:
            grade, comment = "A", "Excellent!"
        elif score >= 70:
            grade, comment = "B", "Good job!"
        elif score >= 50:
            grade, comment = "C", "Not bad."
        elif score >= 30:
            grade, comment = "D", "Keep practicing."
        else:
            grade, comment = "F", "Try again!"

        drawLabel(f"{score:.0f} / 100", RIGHT_PANEL_LABEL_X, 545,
                  size=26, bold=True, font=SCHOOL_FONT)
        drawLabel(f"Grade: {grade}", RIGHT_PANEL_LABEL_X, 580,
                  size=16, bold=True, font=SCHOOL_FONT)
        drawLabel(f"Avg error: ${app.testAvgError:.2f}",
                  RIGHT_PANEL_LABEL_X, 605, size=13, font=SCHOOL_FONT)
        drawLabel(comment, RIGHT_PANEL_LABEL_X, 630,
                  size=14, font=SCHOOL_FONT)
        drawLabel("Press enter to try again",
                  RIGHT_PANEL_LABEL_X, 658,
                  size=11, font=SCHOOL_FONT)
    else:
        # --- Show coverage / submit hint ---
        coverage = computeCoverage(app)
        submitFailed = app.testSubmitMessage is not None

        if submitFailed:
            coverageColor = 'red'
        elif coverage >= COVERAGE_THRESHOLD:
            coverageColor = 'green'
        else:
            coverageColor = 'black'

        drawLabel(f"Coverage: {coverage * 100:.0f}%",
                  RIGHT_PANEL_LABEL_X, 550,
                  size=14, bold=True, font=SCHOOL_FONT, fill=coverageColor)

        if submitFailed:
            drawLabel(f"Need at least {COVERAGE_THRESHOLD*100:.0f}% coverage to submit!",
                      RIGHT_PANEL_LABEL_X, 590,
                      size=12, bold=True, fill='red', font=SCHOOL_FONT)
        else:
            drawLabel("Press ENTER to submit",
                      RIGHT_PANEL_LABEL_X, 590, size=12, font=SCHOOL_FONT)

def drawBackButton():
    drawRect(0, 0, 100, 35, fill='red', opacity=60, border='black')
    drawLabel("BACK", 50, 17.5, align='center', size=15, bold=True,font=SCHOOL_FONT)

# ============= CONTROLLER ===============

def onKeyPress(app, key):
    if app.mode == 'main':
        if app.selectedInput is not None:
            if key == 'enter':
                if app.selectedInput is app.tickerInput:
                    handleTickerLoad(app)
                else:
                    commitTextInput(app, app.selectedInput)
                app.selectedInput.selected = False
                app.selectedInput = None
            elif key == 'escape':
                if app.selectedInput is not app.tickerInput:
                    matching = findSliderById(app, app.selectedInput.id)
                    app.selectedInput.setValueFromNumber(matching.currVal)
                app.selectedInput.selected = False
                app.selectedInput = None
            else:
                app.selectedInput.handleKey(key)
            return

        # toggle between call and put (main mode)
        if key == 'c':
            app.showCall = True
        elif key == 'p':
            app.showCall = False

    elif app.mode == 'test':
        if app.testPhase == 'drawing':
            if key == 'c':
                switchTestOptionType(app, True)
            elif key == 'p':
                switchTestOptionType(app, False)
            elif key == 'enter':
                coverage = computeCoverage(app)
                if coverage < COVERAGE_THRESHOLD:
                    app.testSubmitMessage = (
                        f"Need {COVERAGE_THRESHOLD*100:.0f}% coverage. "
                        f"You have {coverage*100:.0f}%."
                    )
                else:
                    result = gradeTestDrawing(app)
                    if result is not None:
                        app.testScore, app.testAvgError = result
                        app.testPhase = 'grading'
                        app.testSubmitMessage = None

        elif app.testPhase == 'grading':
            if key == 'enter':
                buildTestProblems(app)
                app.testPhase = 'drawing'


def onMousePress(app, mouseX, mouseY):
    if onBackButton(mouseX, mouseY) and app.mode != 'start':
        app.mode = 'start'
        app.testPhase = 'selectLevel'
        return

    if app.mode == 'main':
        # ticker input click
        if app.tickerInput.isMouseOver(mouseX, mouseY):
            for other in app.textInputs:
                other.selected = False
            if app.selectedInput is not None and app.selectedInput is not app.tickerInput:
                app.selectedInput.selected = False
            app.tickerInput.selected = True
            app.selectedInput = app.tickerInput
            return

        # LOAD button click
        if 575 <= mouseX <= 635 and 15 <= mouseY <= 37:
            handleTickerLoad(app)
            return

        # slider text input click
        for textInput in app.textInputs:
            if textInput.isMouseOver(mouseX, mouseY):
                for other in app.textInputs:
                    other.selected = False
                if app.tickerInput.selected:
                    app.tickerInput.selected = False
                textInput.selected = True
                textInput.highlighted = False  # user is taking over
                app.selectedInput = textInput
                return

        # click was empty so deselect
        if app.selectedInput is not None:
            if app.selectedInput is app.tickerInput:
                app.tickerInput.selected = False
                app.selectedInput = None
            else:
                commitTextInput(app, app.selectedInput)
                app.selectedInput.selected = False
                app.selectedInput = None

        # slider click
        for slider in app.sliders:
            if slider.isMouseOver(mouseX, mouseY):
                app.currSlider = slider
                slider.updateValueFromMouse(mouseX)
                recomputePrices(app)
                syncTextInputFromSlider(app, slider)
                return

    elif app.mode == 'start':
        if 150 <= mouseX <= 450 and 200 <= mouseY <= 300:
            app.mode = 'instructions'
        elif 550 <= mouseX <= 850 and 200 <= mouseY <= 300:
            app.mode = 'explanation'
        elif 150 <= mouseX <= 450 and 400 <= mouseY <= 500:
            app.mode = 'main'
        elif 550 <= mouseX <= 850 and 400 <= mouseY <= 500:
            app.mode = 'test'

    elif app.mode == 'test':
        if app.testPhase == 'selectLevel':
            if 145 <= mouseX <= 235:
                for i in range(1, 6):
                    topY = 125 + i * 60
                    bottomY = topY + 30
                    if topY <= mouseY <= bottomY:
                        app.testLevel = i

                        buildTestProblems(app)
                        app.testPhase = 'drawing'
                        return

        elif app.testPhase == 'drawing':
            if inChartArea(mouseX, mouseY):
                app.testUserPoints = []
                app.testDrawing = True
                app.testSubmitMessage = None  # fresh start, clear any warning
                minX, maxX, minY, maxY = app.testChartBounds
                dx, dy = screenToData(mouseX, mouseY, minX, maxX, minY, maxY)
                app.testUserPoints.append((dx, dy))
                return

def onMouseDrag(app, mouseX, mouseY):
    if app.currSlider is not None:
        app.currSlider.updateValueFromMouse(mouseX)
        syncTextInputFromSlider(app, app.currSlider)
        recomputePrices(app)
        return

    if app.mode == 'test' and app.testPhase == 'drawing' and app.testDrawing:
        clampedX = max(PLOT_LEFT, min(PLOT_RIGHT, mouseX))
        clampedY = max(PLOT_TOP, min(PLOT_BOTTOM, mouseY))
        minX, maxX, minY, maxY = app.testChartBounds
        dx, dy = screenToData(clampedX, clampedY, minX, maxX, minY, maxY)
        app.testUserPoints.append((dx, dy))

        # Clear failed-submit warning once they've drawn enough to pass
        if (app.testSubmitMessage is not None
            and computeCoverage(app) >= COVERAGE_THRESHOLD):
            app.testSubmitMessage = None

def onMouseRelease(app, mouseX, mouseY):
    app.currSlider = None
    app.testDrawing = False

def onBackButton(mouseX,mouseY):
    if mouseX <= 100 and mouseY <= 35:
        return True
    return False

# =============== RUN APP =================

def main():
    runApp(width=1010, height=700)
main()
