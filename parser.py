from lark import Lark, Visitor, Transformer, Tree, Token
import os
import sys

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
					return "all(" + children[2] + " " + RangeIter().transform(children[1]).split(':')[0] + ")"
				if children[0].type.lower() == "exists":
					return "any(" + children[2] + " " + RangeIter().transform(children[1]).split(':')[0] + ")"
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
        string = "for " + \
            children[0] + " in range(" + values[0] + ", " + values[1] + "+1" + "): "
        return string


class Code(Transformer):
	def code(self, children):
		variable = []
		if (isinstance(children[0], Token)):
			if (children[0].type.lower() == "foreach"):
				variable.append(RangeIter().transform(children[1]))
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
		decls = Decls().transform(children[0])
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
	codeString = "class %s:"%fileName

	for function in functions:
		codeString += '\n'
		codeString += prettyPrint(function, 1)

	open("generated/%s.py"%fileName, "w+").write(codeString)
