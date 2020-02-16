"""
<Filename>
  variables/__init__.py

<Purpose>
  This is the main module file for the variables seash module.  It provides
  users with the ability to set custom variables and then retrieve their values
  for future use.

  It implements the following commands:
    set [variable name] [variable value]
    show variables
"""

# Needed so that we can relay user errors to seash for printing
import seash_exceptions


# Keeps track of user defined variables
# Maps a variable name (string) to a value (string)
uservariables = {}


help_text = """
Variables Module

This module allows you to define variables that you can access later using the
'set' command.  Variable names cannot contain spaces.  Values are automatically
stripped of leading/trailing whitespace.  To set a new variable, use the 
following syntax:

  user@! > set uploadfn theverylonguploadfile.txt

You reference the variable by typing '$' and then the variable name.
Optionally you can also mark the end of a variable by using yet another '$'.

  user@! > on %1 upload $uploadfn
  user@! > on %1 upload dir/$uploadfn
  user@! > on %1 upload dir/$username$/password

If you need to use the $ symbol, you can mark that by using 2 subsequent $'s.
For example, if you type the following:
  user@! > on %1 run need_dollarsign_arg.r2py $$ username

It is converted to:
  user@! > on %1 run need_dollarsign_arg.r2py $ username  

Escaping is optional for a single $ at the end of the string.  The following 
two commands are interpreted as identical commands.

  user@! > on %1 run need_dollarsign_arg.r2py $$
  user@! > on %1 run need_dollarsign_arg.r2py $

"""


def set_user_variable(input_dict, environment_dict):
  """
  <Purpose>
    Seash callback to allow user to define a custom variable and assign a value
    to it.
  <Arguments>
    input_dict: Input dictionary generated by seash_dictionary.parse_command().
    environment_dict: Dictionary describing the current seash environment.
    
    For more information, see command_callbacks.py's module docstring.
  <Side Effects>
    A new variable will be added to the uservariables dictionary.
  <Exceptions>
    UserError: The user did not provide a value to assign to the variable
  <Return>
    None
  """
  # Iterates through the dictionary to retrieve the variable name
  command_key = input_dict.keys()[0]
  while input_dict[command_key]['name'] is not 'variable_name':
    input_dict = input_dict[command_key]['children']
    variable_name = command_key = input_dict.keys()[0]

  # User may accidentally omit this value, we must catch the exception and
  # return something readable...
  try:
    # Iterates through the dictionary to retrieve the variable value
    while input_dict[command_key]['name'] is not 'variable_value':
      input_dict = input_dict[command_key]['children']
      variable_value = command_key = input_dict.keys()[0]
  except IndexError, e:
    raise seash_exceptions.UserError("Error, expected a value to assign to variable")

  uservariables[variable_name] = variable_value.strip()



def show_user_variables(input_dict, environment_dict):
  """
  <Purpose>
    Seash callback to allow user to check all variables that they defined.
  <Arguments>
    input_dict: Input dictionary generated by seash_dictionary.parse_command().
    environment_dict: Dictionary describing the current seash environment.
    
    For more information, see command_callbacks.py's module docstring.
  <Side Effects>
    All the variables currently defined will be printed alongside their values.
  <Exceptions>
    None
  <Return>
    None
  """
  for variable, value in uservariables.iteritems():
    print variable+": '"+value+"'"


def preprocess_user_variables(userinput):
  """
  <Purpose>
    Command parser for user variables.  Takes the raw userinput and replaces
    each user variable with its set value.
  <Arguments>
    userinput: A raw user string
  <Side Effects>
    Each user variable will be replaced by the value that it was previously
    set to.
  <Exceptions>
    UserError: User typed an unrecognized or invalid variable name
  <Returns>
    The preprocessed string
  """
  retstr = ""
  while '$' in userinput:
    text_before_variable , variable_delimiter, userinput = userinput.partition('$')
    retstr += text_before_variable

    # Treat $$ as an escape for a single $.
    # Also escape if there is nothing left
    if not userinput or userinput.startswith('$'):
      retstr += '$'
      userinput = userinput[1:]
      continue

    # Look for the next space, or the next $.  The closest one of these will be
    # used as the delimiter.  Then update the remaining user input.
    space_variable_length = userinput.find(' ')
    dollarsign_variable_length = userinput.find('$')

    # If the length is -1, then the delimiter was not found.
    # We use the length of the entire string to represent this.
    # If there was one delimiter found, then that delimiter's value
    # will always be less than the string's length.
    # If it is a tie, then it simply means that the entire string
    # is the variable name.
    if space_variable_length == -1:
      space_variable_length = len(userinput)
    if dollarsign_variable_length == -1:
      dollarsign_variable_length = len(userinput)

    variable_length = min(space_variable_length, dollarsign_variable_length)
    variable_name = userinput[:variable_length]
    userinput = userinput[variable_length + 1:]  # Skip the actual delimiter

    # Perform the replacement!
    # User may type in a variable that has not yet been defined
    try:
      retstr += uservariables[variable_name]
    except KeyError:
      raise seash_exceptions.UserError("Variable does not exist: "+variable_name)

    # The user expects a space before the string right after the variable.
    # e.g. 'loadkeys $myname as awesome' should turn into
    #      'loadkeys theusername as awesome'
    if space_variable_length < dollarsign_variable_length:
      retstr += ' '

  # Now add the remaining text after the last variable
  else:
    retstr += userinput

  return retstr


def autocomplete(input_list):
  """
  <Purpose>
    Returns all valid input completions for the specified command line input.

  <Arguments>
    input_list: A list of tokens.

  <Side Effects>
    None

  <Exceptions>
    None

  <Returns>
    A list of strings representing valid completions.
  """
  # We are only interested if the last token starts with a single '$'
  # Double $$'s indicate that it is meant to be a '$', so we don't do anything.
  if input_list[-1].startswith('$') and not input_list[-1].startswith('$$'):
    # Omit the '$'
    partial_variable = input_list[-1][1:]
    commands = []

    for variable in uservariables:
      # No need to include variables that don't match...
      if variable.startswith(partial_variable):
        # Reconstruct the string
        tokens = input_list[:-1] + ['$'+variable]
        commands.append(' '.join(tokens))
    return commands
  return []



command_dict = {
  'set': {'children': {
    '[ARGUMENT]': {'name':'variable_name', 'callback':set_user_variable, 'help_text':'', 'summary': 'Sets a custom user variable.', 'children':{
      '[ARGUMENT]': {'name':'variable_value', 'callback':None, 'help_text':'', 'children':{}}
    }},
  }},
  'show': {'children': {
    'variables': {'name': 'variables', 'callback':show_user_variables, 'help_text':'', 'summary':"Display a list of user defined variables.", 'children': {}}
  }}
}


# This is where the module importer loads the module from
moduledata = {
  'command_dict': command_dict,
  'help_text': help_text,
  'url': None,
  'input_preprocessor': preprocess_user_variables,
  'tab_completer': autocomplete
}
