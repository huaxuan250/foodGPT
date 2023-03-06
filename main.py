from bs4 import BeautifulSoup
import requests
import re
import nltk
nltk.download('punkt')
from unicodedata import numeric
from pyfood.utils import Shelf
import warnings
warnings.filterwarnings("ignore")

ACTIONS = {
        'whip': ['whip'],
        'broil': ['broil'],
        'cut': ['cut'],
        'chop': ['chop'],
        'stir fry': ['stir-fry', 'stir fry', 'stir fried', 'stir-fried'],
        'saute': ['saute', 'sauté'],
        'braise': ['braise', 'braising'],
        'sear' : ['sear'],
        'grill' : ['grill'],
        'roast': ['roast'],
        'simmer': ['simmer', 'simmered'],
        'poach': ['poach', 'poached'],
        'boil': ['boil', 'boiled'],
        'bake': ['bake', 'baking'],
        'deep fry': ['deep-fry', 'deep fry', 'deep fried', 'deep-fried'],
        'stew': ['stew'],
        'steam': ['steam'],
        'broil': ['broil'],
        'blanch': ['blanch'],
        'slice': ['slice'],
        'shred': ['shred'],
        'dice': ['dice'],
        'divide': ['divide'],
        'mince': ['mince'],
        'crush': ['crush'],
        'blend': ['blend'],
        'squeeze': ['squeeze'],
        'peel': ['peel'],
        'stir': ['stir'],
        'mix': ['mix'],
        'whisk': ['whisk'],
        'drain': ['drain'],
        'strain': ['strain'],
        'marinate': ['marinate'],
        'brush': ['brush'],
        'freeze': ['freeze'],
        'cool': ['cool'],
        'caramelize': ['caramelize'],
        'preheat': ['preheat', 'pre-heat', 'pre heat'],
        'sous vide': ['sous vide', 'sous-vide'],
        'shallow fry': ['shallow-fry', 'shallow fry', 'shallow fried', 'shallow-fried'],
        'fry': ['fry', 'fried']
}

'''
Helper Functions
'''
def convert_str_to_float(x):

    digit = 0.0
    fraction = 0.0

    if len(x) > 1:
        if not x[-1].isdigit():
            fraction = numeric(x[-1])
            digit = int(x[:-1])
        else:
            digit = int(x)
    else:
        if not x.isdigit():
            fraction = numeric(x)
        else:
            digit = int(x)
    
    number = digit + fraction
    
    return number

'''
Main Component Functions:
'''
def get_soup(url):
  headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
  html = requests.get(url, headers = headers)
  soup = BeautifulSoup(html.content,'html.parser')
  return soup

def get_ingredients(soup):
  html_items = soup.find_all("li","mntl-structured-ingredients__list-item")
  ingredients = []

  for item in html_items:
    text = item.text[1:-1]
    ingredients.append(text)

  return ingredients

def get_instructions(soup):
  instructions_steps = soup.find_all("li", {"class": 'comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup'})
  instructions = []

  for instruction in instructions_steps:
    text = instruction.find('p').text
    text = text[1:-1]
    instructions.append(text)
  
  return instructions

def subdivide_instructions(instructions):
  steps = []
  for instruction in instructions:
    sub_instructions = nltk.tokenize.sent_tokenize(instruction)
    for sub in sub_instructions:
      steps.append(sub)
  return steps

def extract_actions(step):
  action_results = []

  first_action = step.split(" ")[0].lower()
  action_results.append(first_action)
  
  for action in ACTIONS.keys():
    for variation in ACTIONS[action]:
      if variation in step.lower():
        action_results.append(action)

  # 3rd Case: then/and followed by a verb
  # Ignore it for now bruh
  
  return list(set(action_results))

def extract_time(step):
  words = nltk.tokenize.wordpunct_tokenize(step.lower())

  unit = ''
  unit_loc = 0
  for idx, word in enumerate(words):
    if 'hour' in word:
      unit = 'hour'
      unit_loc = idx
    elif 'minute' in word:
      unit = 'minute'
      unit_loc = idx
    elif 'second' in word:
      unit = 'second'
      unit_loc = idx
  
  time = ''
  time_loc = 0
  if unit:
    time_loc = unit_loc - 1
    if words[time_loc].isdigit():
      time = words[time_loc]
      if int(time) > 1:
        unit = unit + 's'
  
  if time and unit:
    return " ".join([time, unit])
  else:
    return []

def extract_temp(step):
  words = nltk.tokenize.wordpunct_tokenize(step.lower())

  degree_idx = 0
  for idx, word in enumerate(words):
    if "degree" in word:
      degree_idx = idx
      break
  
  answer = []
  if degree_idx != 0:
    answer.append(words[degree_idx-1])
    answer.append(words[degree_idx])
    answer.append(words[degree_idx+1])
  
  return " ".join(answer)

def extract_food_name(command):
  shelf = Shelf()
  results = shelf.process_ingredients([command])
  if results['ingredients']:
    return results['ingredients'][0]['foodname']
  elif results['HS']:
    return results['HS'][0]
  else:
    return None
  
'''
Dialogue Handling Functions:
'''
def handle_all_steps(command):
  command = command.lower()
  intentions = ["show", "display", "see"]
  if "step" in command and "all" in command:
    for intention in intentions:
      if intention in command:
        return True
  return False
  
def handle_all_ingredients(command):
  command = command.lower()
  intentions = ["show", "display", "see"]
  if "ingredients" in command and "all" in command:
    for intention in intentions:
      if intention in command:
        return True
  return False

def if_navigate(command):
  command = command.lower()
  intentions = ['next','back','previous','start','navigate','repeat', 'take']
  for intention in intentions:
    if intention in command:
      return True
  return False

def jump_navigate(command, curr):
  command = command.lower()
  if 'next' in command:
    return curr + 1
  elif 'back' in command or 'previous' in command:
    return curr - 1
  elif 'take' in command:
    matched = re.search(r'\d{1,2}(?:st|nd|rd|th)', command)
    if matched:
      order = matched.group(0)
      order = int(order[:-2])
      order = order - 1 
    return order
  else:
    return curr

def if_general_question(command):
  command = command.lower()
  intentions = ["how to", "how do i", "what is a"]
  for intention in intentions:
    if intention in command:
      return True
  return False

def answer_general_question(command, step):
  command = command.lower()
  answer = ""
  if "that" in command:
    action = extract_actions(step)[0]
    command = "how to " + action
  
  query = command.split()
  query = "+".join(query)
  base = "https://www.google.com/search?q="
  return base+query

def if_specific_question(command):
  command = command.lower()
  intentions = ["how much", "temperature","how long",'when']
  for intention in intentions:
    if intention in command:
      return True
  return False

def answer_specific_question(command, step, ingredients):
  command = command.lower()

  if 'how much' in command:
    # Find the best match ingredient
    target_food = extract_food_name(command)
    if target_food:
      for igd in ingredients:
        if target_food in igd:
          return igd
    return "No available food information on that food."
  elif 'temperature' in command:
    target_temp = extract_temp(step)
    if target_temp:
      return target_temp
    else:
      return 'No available information on temperature.'
  elif 'how long do i' in command or 'when' in command:
    target_time = extract_time(step)
    if target_time:
      return target_time
    else:
      return 'No available information on time.'
  
  return 'Cannot understand your command'

def if_sub_food(command):
  command = command.lower()
  if 'substitute' in command:
    return True
  else:
    return False


def get_food_sub(command):

  food_name = extract_food_name(command)

  shelf = Shelf()
  target_food = shelf.get_food_info(food_name)

  if not target_food:
    return []

  target_taxon = target_food[2]
  all_foods = list(shelf.feats.items())

  results = []
  for food in all_foods:
    _, info = food
    food_taxon = info['taxon']

    if target_taxon == food_taxon:
      results.append(info['en'])

  return results


'''
User Interface Components
'''
def construct_recipe(url):
  soup = get_soup(url)
  raw_ingredients = get_ingredients(soup)
  raw_steps = get_instructions(soup)
  
  steps = subdivide_instructions(raw_steps)

  return steps, raw_ingredients

def accept_url():
  while True:
    url = input("Please input a url from AllRecipes.com: \n\n")
    split_url = url.split("/")
    if split_url[2] != 'www.allrecipes.com':
      print("Please provide a recipe from AllRecipes.com\n")
    else:
      return url

def user_interface():
  # Interface happens here
  url = accept_url()
  steps, items = construct_recipe(url)

  curr_idx = 0
  while True:
    command = input("What would you like to do or know about?:\n")

    # Show all steps
    if handle_all_steps(command):
      for idx, step in enumerate(steps):
        print("Step " + str(idx) + ":", step, '\n')

    # Show all ingredients
    elif handle_all_ingredients(command):
      for ingredient in items:
        print(ingredient, '\n')

    # Naigation Module, curr_idx is modified here
    elif if_navigate(command):
      curr_idx = jump_navigate(command, curr_idx)
      if curr_idx < 0:
        curr_idx = 0
        print("This is the first step\n")
      elif curr_idx >= len(steps):
        curr_idx == len(steps) - 1
        print("This is the last step\n")
      else:
        print("Current step: ", steps[curr_idx],'\n')
    
    # Checking if this is a general question
    elif if_general_question(command):
      answer = answer_general_question(command, steps[curr_idx])
      print(answer, '\n')
    
    # Checking if this is a specific question
    elif if_specific_question(command):
      answer = answer_specific_question(command, steps[curr_idx], items)
      print(answer, '\n')
    
    # Checking if this is about substitution
    elif if_sub_food(command):
      answer = get_food_sub(command)
      print(answer, '\n')


def main():
  user_interface()

if __name__ == "__main__":
  main()