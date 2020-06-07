from lark import Lark, Visitor, Transformer, Tree, Token
import os
import sys


def generateRandomFunction(rangeIters):
	randomFunction = ["def random(self):"]
	functionContent = ["state = self.initialState()"]
	functionContent.append("while not self.finalState(state):")
	whileContent = []
	ids = [rangeIter[0] for rangeIter in rangeIters]
	for rangeIter in rangeIters:
		whileContent.append("%s = random.randint(%s, %s)"%(rangeIter[0], rangeIter[1], rangeIter[2]))
	paramString = "".join([", %s"%id for id in ids])
	whileContent.append("newState = self.transition(copy.deepcopy(state)%s)"%paramString)
	whileContent.append("if self.validTransition(copy.deepcopy(state)%s) and self.validState(newState):"%paramString)
	whileContent.append(["state = newState"])
	functionContent.append(whileContent)
	functionContent.append("return state")
	randomFunction.append(functionContent)
	return randomFunction


def generateImprovedRandomFunction(rangeIters):
	randomFunction = ["def improvedRandom(self, maxNrOfSteps = float('inf')):"]
	functionContent = ["state = self.initialState()"]
	functionContent.append("visitedStates = [state]")
	functionContent.append("nrOfSteps = 0")
	functionContent.append("while not self.finalState(state):")
	whileContent = []
	ids = [rangeIter[0] for rangeIter in rangeIters]
	for rangeIter in rangeIters:
		whileContent.append("%s = random.randint(%s, %s)"%(rangeIter[0], rangeIter[1], rangeIter[2]))
	paramString = "".join([", %s"%id for id in ids])
	whileContent.append("newState = self.transition(copy.deepcopy(state)%s)"%paramString)
	whileContent.append("nrOfSteps += 1")
	whileContent.append("if newState not in visitedStates and self.validTransition(copy.deepcopy(state)%s) and self.validState(newState):"%paramString)
	whileContent.append(["state = newState"])
	whileContent.append(["visitedStates.append(state)"])
	whileContent.append("if nrOfSteps > maxNrOfSteps:")
	whileContent.append(["state = self.initialState()"])
	whileContent.append(["visitedStates = [state]"])
	whileContent.append(["nrOfSteps = 0"])
	functionContent.append(whileContent)
	functionContent.append("return state")
	randomFunction.append(functionContent) 
	return randomFunction


def generateBackTrackingFunction(rangeIters):
	backtrackingFunction = ["def backtracking(self, state, visitedStates):"]
	firstList = []
	latestList = firstList
	for rangeIter in rangeIters:
		newList = ["for %s in range(%s, %s+1):"%(rangeIter[0], rangeIter[1], rangeIter[2])]
		latestList.append(newList)
		latestList = newList

	paramString = "".join([", %s"%id for id in [rangeIter[0] for rangeIter in rangeIters]])

	forContent = []
	forContent.append("newState = self.transition(copy.deepcopy(state)%s)"%paramString)
	forContent.append("if newState not in visitedStates and self.validTransition(copy.deepcopy(state)%s) and self.validState(newState):"%paramString)
	forContent.append(["if (self.finalState(newState)):", ["return state"]])
	forContent.append(["else:", ["visitedStates.append(newState)", "self.backtracking(newState, visitedStates)"]])
	
	latestList.append(forContent)
	backtrackingFunction.append(firstList[0])

	return backtrackingFunction


class BasicFunctions(Transformer):
	def basicfunctions(self, children):
		if (children[0].type.lower() == "size"):
			return str(children[0]) + "(" + children[1] + ")"
		elif (children[0].type.lower() == "append"):
			return Exp().transform(children[1]) + ".append(" + Exp().transform(children[2]) + ")"


class Exp(Transformer):
	def exp(self, children):
		if (len(children) == 0):
			return "[]"
		elif isinstance(children[0], Token):
			if children[0].type.lower() == "number":
				return str(children[0])
			elif children[0].type.lower() == "id":
				return str(children[0])
			elif children[0].type.lower() == "instance":
				return "self." + str(children[1])
		else:
			if isinstance(children[0], Tree) and children[0].data == "basicfunctions":
				return BasicFunctions().transform(children[0])
			elif isinstance(children[1], Token) and children[1].type.lower() == "operation":
				return children[0] + str(children[1]) + children[2]
			else:
				return children[0] + '[' + children[1] + ']'


class Bool(Transformer):
	def bool(self, children):
		if len(children) > 1:
			if isinstance(children[1], Token):
				if children[1].type.lower() == 'booloperation':
					children[0] = Exp().transform(children[0])
					children[2] = Exp().transform(children[2])
					return children[0] + str(children[1]) + children[2]
				elif children[1].type.lower() == 'and':
					return children[0] + ' and ' + children[2]
				elif children[1].type.lower() == 'or':
					return children[0] + ' or ' + children[2]
			elif isinstance(children[0], Token):
				if children[0].type.lower() == 'not':
					return 'not ' + children[1]
				if children[0].type.lower() == "forall":
					string = "all(" + children[2] + " "
					rangeValues = RangeIter().transform(children[1])
					string += "for " + rangeValues[0] + " in range(" + rangeValues[1] + ", " + rangeValues[2] + "+1))"
					return string
				if children[0].type.lower() == "exists":
					string = "any(" + children[2] + " "
					rangeValues = RangeIter().transform(children[1])
					string += "for " + rangeValues[0] + " in range(" + rangeValues[1] + ", " + rangeValues[2] + "+1))"
					return string
		else:
			if isinstance(children[0], Token):
				return str(children[0])
			return "(" + children[0] + ")"
		return None


class Range(Transformer):
    def range(self, children):
        exp1 = Exp().transform(children[0])
        exp2 = Exp().transform(children[1])
        return (exp1, exp2)


class RangeIter(Transformer):
	def rangeiter(self, children):
		values = Range().transform(children[1])
		values = (str(children[0]), *values)
		return values


class RangeIters(Transformer):
	def rangeiters(self, children):
		if (len(children) == 1):
			return [RangeIter().transform(children[0])]
		else:
			return [RangeIter().transform(children[0])] + children[1]

class Code(Transformer):
	def code(self, children):
		variable = []
		if (isinstance(children[0], Token)):
			if (children[0].type.lower() == "foreach"):
				rangeValues = RangeIter().transform(children[1])
				string = "for " + \
					rangeValues[0] + " in range(" + rangeValues[1] + ", " + rangeValues[2] + "+1): "
				variable.append(string)
				variable += children[2]
			elif (children[0].type.lower() == "return"):
				variable.append("return " + children[1])
			elif (children[0].type.lower() == "if"):
				variable.append("if (" + Bool().transform(children[1]) + "):")
				variable.append(CodeBlock().transform(children[2]))
				if (len(children) > 3):
					variable.append("else:")
					variable.append(CodeBlock().transform(children[4]))
			elif (children[0].type.lower() == "while"):
				variable.append("while (" + Bool().transform(children[1]) + "):")
				variable.append(CodeBlock().transform(children[2]))
		else:
			if (children[0].data == "basicfunctions"):
				variable.append(BasicFunctions().transform(children[0]))
			else: variable.append(Exp().transform(children[0]) + '=' + Exp().transform(children[1]))
		return variable


class CodeBlock(Transformer):
	def codeblock(self, codeBlockChildren):
		code = []
		for child in codeBlockChildren:
			if isinstance(child, Tree):
				code.append(Code().transform(child))
			else: code += child
		return code


class Decl(Transformer):
    def decl(self, children):
        return str(children[0])


class Decls(Transformer):
	def decls(self, children):
		declarations = ""
		for decl in children:
			if isinstance(decl, Tree):
				if declarations != "":
					declarations += ", "
				declarations += Decl().transform(decl)
			else:
				if declarations != "":
					declarations += ", "
				declarations += decl
		return declarations


class FinalState(Transformer):
	def finalstate(self, children):
		variable = []
		function = "def finalState(self, "  # TODO: rename variable
		function += Decls().transform(children[0])
		function += "):"
		variable.append(function)
		variable.append(["return " + Bool().transform(children[1])])
		return variable


class ValidState(Transformer):
	def validstate(self, children):
		variable = []
		function = "def validState(self, "  # TODO: rename variable
		function += Decl().transform(children[0])
		function += "):"
		variable.append(function)
		variable.append(["return " + Bool().transform(children[1])])
		return variable


class InitialState(Transformer):
	def initialstate(self, children):
		variable = []
		function = "def initialState(self"  # TODO: rename variable
		if (children[0].data == "decls"):
			function += ", " + Decls().transform(children[0])
			function += "):"
			variable.append(function)
			variable += (CodeBlock().transform(children[1]))
		else:
			function += "):"
			variable.append(function)
			variable += (CodeBlock().transform(children[0]))
		return variable


class Transition(Transformer):
	def transition(self, children):
		variable = []
		function = "def transition(self, "  # TODO: rename variable
		function += Decls().transform(children[0])
		function += "):"
		variable.append(function)
		variable += (CodeBlock().transform(children[1]))
		return variable


class ValidTransition(Transformer):
	def validtransition(self, children):
		variable = []
		function = "def validTransition(self, "  # TODO: rename variable
		function += Decls().transform(children[0])
		function += "):"
		variable.append(function)
		variable.append(["return " + Bool().transform(children[1])])
		return variable


class Instance(Transformer):
	def instance(self, children):
		variable = []
		function = "def __init__(self, "  # TODO: rename variable
		function += Decls().transform(children[0])
		function += "):"
		variable.append(function)
		variable += (CodeBlock().transform(children[1]))
		return variable


class Strategy(Transformer):
	def strategy(self, children):
		if (children[0].type.lower() == "random"):
			return generateRandomFunction(RangeIters().transform(children[1]))
		elif (children[0].type.lower() == "improvedrandom"):
			return generateImprovedRandomFunction(RangeIters().transform(children[1]))
		elif (children[0].type.lower() == "backtracking"):
			return generateBackTrackingFunction(RangeIters().transform(children[1]))


class Specification(Transformer):
	def specification(self, children):
		data = []
		for child in children:
			if (child.data == "instance"):
				data.append(Instance().transform(child))
			elif (child.data == 'initialstate'):
				data.append(InitialState().transform(child))
			elif (child.data == 'validstate'):
				data.append(ValidState().transform(child))
			elif (child.data == 'finalstate'):
				data.append(FinalState().transform(child))
			elif (child.data == 'transition'):
				data.append(Transition().transform(child))
			elif (child.data == 'validtransition'):
				data.append(ValidTransition().transform(child))
			elif (child.data == 'strategy'):
				data.append(Strategy().transform(child))
				# Strategy().transform(child)
		return data


def prettyPrint(lines, nrOfIndents):
	string = ''
	for line in lines:
		if (isinstance(line, str)):
			strLine = ''
			for i in range(0, nrOfIndents):
				strLine += '\t'
			strLine += line
			string += strLine
			string += '\n'
		else:
			string +=prettyPrint(line, nrOfIndents+1)
	return string


parser = Lark(open('grammer.lark'), start='specification')


fileNames = [sys.argv[i] for i in range(1, len(sys.argv))]

if (len(fileNames) != 0):
	if not os.path.isdir('generated'):
		os.mkdir('generated')

for fileName in fileNames:
	tree = parser.parse(open('models/%s.aim'%fileName).read())
	functions = Specification().transform(tree)
	codeString = "import random, copy\n\n"
	codeString += "class %s:"%fileName

	for function in functions:
		codeString += '\n'
		codeString += prettyPrint(function, 1)
	codeString += '\n'

	open("generated/%s.py"%fileName, "w+").write(codeString)
