import json
import csv
import re
import time
import random
from copy import deepcopy

'''
To use, import functions from this file and run the following:
from wordle import get_lists, check_guess, guess_wordle, guess_all_wordles, guess_openers, get_next_guess, get_second_guesses, guess_seconds

# Get the needed lists:
answers, allowed, allowed_freq = get_lists()

To solve a single wordle puzzle:
    # Get a random answer to guess against
    answer = answers[random.randrange(len(answers))]
    # Guess wordle using an opener ('slate' in this case)
    result = guess_wordle(allowed, answer, 'slate')
    # Result returns num guesses it took to solve and state at each step

To check how well an opener would perform (num of guesses to solve) against all possible answers:
    # create a solutions dict to store results
    # cnt of # puzzles solved in X guesses; 7 means could not solve puzzle; -1 means opener was not a valid answer
    solutions = {-1: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6:[], 7:[]}
    # Use opener to guess against all wordle answers
    result = guess_all_wordles(answers, words, solutions, opener)

To check a list of possible openers against all possible answers:
    # In this case list of openers is all allowable guesses
    # guess_all_wordles function takes ~ 5 sec to run
    results = guess_openers(allowed, answers, allowed)
'''

def get_lists():
    # Import a list of words with usage frequency (333,333 english words)
    words, total_frequency = get_wordlist()
    # Imports the complete list of wordle answers from the wordle source code
    answers = get_wordle_answers()
    # Imports the complete list of allowable guesses from the wordle source code
    allowed = get_wordle_allowable()
    # Combine the two lists to create the complete allowable guesses list
    allowed.extend(answers)
    allowed_freq = {}
    for word in allowed:
        allowed_freq[word] = words[word] / total_frequency if words.get(word) else 0
    allowed = sorted(allowed_freq, key=lambda word: allowed_freq[word])
    allowed.reverse()
    print("{} guessable words in dict. {} solutions".format(len(allowed_freq), len(answers)))

    return answers, allowed, allowed_freq
    

def check_guess(guess, rights, wrongs, excludes, answer):
    ''' This is the equivalent of the green, yellow and grey square feedback in the Wordle UI 
        Puts the results in regex '''
    regex = ""

    for i in range(5):
        # If letter is in correct position
        if guess[i] == answer[i]:
            rights.append(guess[i])
            regex += guess[i]
        # if letter is in word, but in wrong position
        elif guess[i] in answer:
            rights.append(guess[i])
            excludes[i].append(guess[i])
            regex += "[^{}]".format("".join(excludes[i]))
        # if letter is NOT in word
        else:
            wrongs.append(guess[i])
            if len(excludes[i]) > 0:
                regex += "[^{}]".format("".join(excludes[i]))
            else:
                regex += "."

    # Letters not in word are excluded separately. Regex handles correct letters or letters NOT in a specific position but still in the word
    return regex

def get_next_guess(guesses, rights, wrongs, regex):
    ''' Based on latest criteria:
        - letters that are IN the word (rights list)
        - letters that are NOT in the word (wrongs list)
        - letters that must be in a specific spot or letters must NOT be in a specific spot (regex)
        Get the next most frequently used word that matches above criteria 
    '''
    new_guesses = []

    # guesses list is sorted by usage frequency (most frequently used words are first)
    # loop through the list until find first word (most frequently used) that matches the criteria
    for word in guesses:
        has_wrong = False
        for w in wrongs:
            if w in word:
                # if the next most frequent word has a letter that is confirmed NOT to be in the answer, skip it
                has_wrong = True
                break
        if not has_wrong:
            has_all = True
            for r in rights:
                if r not in word:
                    # if the next most frequent word does NOT have a letter that is confirmed IN the answer, skip it
                    has_all = False
                    break
            if has_all:
                # if the next most frequent word matches the regex, then it is a valid next guess, return it
                if re.match(regex, word):
                    return word

    return None

def guess_wordle(words, answer, first_guess='slate', second_guess=None):
    ''' Function to guess a single wordle answer 
        Algorithm is to guess the most frequently used word that matches criteria from previous guesses (see get_next_guess)
        Takes in a possible of guesses (words list), which is the same list of allowable guesses from wordle source code
    '''
    g = [{'guess': None, 'rights': [], 'wrongs': [], 'excludes': [[], [], [], [], []], 'regex': '.....'} for i in range(6)]
    rights = []
    wrongs = []
    excludes = [[], [], [], [], []]

    for i in range(6):
        # first guess
        if i == 0:
            g[i]['guess'] = first_guess
        elif i == 1 and second_guess:
            g[i]['guess'] = second_guess
        else:
            g[i]['guess'] = get_next_guess(words, rights, wrongs, g[i]['regex'])

        # print("starting guess {} - {}".format(i+1, guesses[i]['guess']))
        if g[i]['guess'] == answer:
            # print("Solution Found: {}".format(guesses[i]['fivers'][0]))
            num = i+1
            return {'num': num, 'solution': answer, 'guesses': g}
        elif not g[i]['guess']:
            # NO solutions, word list doesn't have solution
            # print("NO solutions, word list doesn't have solution")
            num = -1
            return {'num': num, 'solution': answer, 'guesses': g}
        elif i >= 5:
            # NO solutions, word list doesn't have solution
            # print("NO solution, ran out of guesses")
            num = 7
            return {'num': num, 'solution': answer, 'guesses': g}
        else:
            # keep guessing
            # g[i+1]['excludes'] = g[i]['excludes']
            g[i+1]['regex'] = check_guess(g[i]['guess'], rights, wrongs, excludes, answer)
            g[i+1]['rights'] = rights.copy()
            g[i+1]['wrongs'] = wrongs.copy()
            g[i+1]['excludes'] = deepcopy(excludes)


def guess_all_wordles(answers, words, solutions, first_guess='slate', second_guess=None):
    ''' function to loop through all wordle answers and use he guess_wordle function
        Records number of guesses it took
        Takes in an opener or defaults to using 'slae'
    '''
    t = time.time()
    cnt = 1
    for answer in answers:
        print("starting wordle {} / {}".format(cnt, len(answers)), end='\r')
        result = guess_wordle(words, answer, first_guess, second_guess)
        solutions[result['num']].append(result)
        cnt += 1

    print("Took {} sec".format(time.time() - t))

    results = {'t': time.time() - t}
    for k, v in solutions.items():
        print(k, len(v))
        results[k] = len(v)

    return results

def get_second_guesses(solutions):
    results = []
    for k in solutions:
        print("on {}".format(k))
        if k < 0 or k > 6:
            print("breaking")
            break
        for s in solutions[k]:
            result =['slate']
            result.append(s['guesses'][k-1]['guess'])
            result.append(k)
            result.append(','.join(s['guesses'][k-1]['wrongs']))
            result.append(','.join(s['guesses'][k-1]['rights']))
            result.append(','.join(s['guesses'][k-1]['excludes'][0]))
            result.append(','.join(s['guesses'][k-1]['excludes'][1]))
            result.append(','.join(s['guesses'][k-1]['excludes'][2]))
            result.append(','.join(s['guesses'][k-1]['excludes'][3]))
            result.append(','.join(s['guesses'][k-1]['excludes'][4]))
            results.append(result)

    return results

def guess_seconds(seconds, answers, words, opener='slate'):
    results = []
    cnt = 1
    for second in seconds:
        print("{} / {}".format(cnt, len(seconds)))
        solutions = {-1: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6:[], 7:[]}
        result = guess_all_wordles(answers, words, solutions, opener, second)
        results.append({'opener': opener, 'second': second, 'results': result})
        cnt += 1

    return results

def guess_openers(openers, answers, words):
    ''' Function to loop through a list of openers and use each opener to guess all wordle answers
        Returns the aggregate of number guesses took to solve
        Which can be used to measure how well an opener would perform against all possible answers using the guess_wordle function
    '''
    results = []
    cnt = 1
    for opener in openers:
        print("{} / {}".format(cnt, len(openers)))
        solutions = {-1: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6:[], 7:[]}
        result = guess_all_wordles(answers, words, solutions, opener)
        results.append({'opener': opener, 'results': result})
        cnt += 1

    return results

def save_opener_results(results, fn='results.csv'):
    with open(fn, 'a') as f:
        wr = csv.writer(f, quoting=csv.QUOTE_ALL)
        for res in results:
            wr.writerow([res['opener'], res['results']['t'], (res['results'][1]+res['results'][2]*2+res['results'][3]*3+res['results'][4]*4+res['results'][5]*5+res['results'][6]*6)/(res['results'][1]+res['results'][2]+res['results'][3]+res['results'][4]+res['results'][5]+res['results'][6]), res['results'][1], res['results'][2], res['results'][3], res['results'][4], res['results'][5], res['results'][6], res['results'][7], res['results'][-1]])

    return fn

def save_seconds_results(results, fn='seconds.csv'):
    with open(fn, 'a') as f:
        wr = csv.writer(f, quoting=csv.QUOTE_ALL)
        for res in results:
            wr.writerow([res['opener'], res['second'], res['results']['t'], (res['results'][1]+res['results'][2]*2+res['results'][3]*3+res['results'][4]*4+res['results'][5]*5+res['results'][6]*6)/(res['results'][1]+res['results'][2]+res['results'][3]+res['results'][4]+res['results'][5]+res['results'][6]), res['results'][1], res['results'][2], res['results'][3], res['results'][4], res['results'][5], res['results'][6], res['results'][7], res['results'][-1]])

    return fn

def get_wordle_answers(fn='wordle_answers.js'):
    with open(fn) as f:
        wordles = json.load(f)

    return wordles

def get_wordle_allowable(fn='wordle_allowed.js'):
    with open(fn) as f:
        allowed = json.load(f)

    return allowed

def get_wordlist(fn='words1.txt', num=-1):
    words = {}
    total_frequency = 0
    cnt = 0
    with open(fn) as f:
        for line in f.readlines():
            words[line.split()[0].lower()] = int(line.split()[1])
            total_frequency += int(line.split()[1])
            cnt += 1
            if num > 0 and cnt >= num:
                break

    return words, total_frequency
