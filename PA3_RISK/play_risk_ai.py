#Play some ai's against each other in a game
import sys
import imp
import risktools
import time
import os
import random

def print_usage():
    print 'USAGE: python play_risk_ai.py ai_1 name_1 ai_2 name_2 . . . a_n name_n  (where n is 7 or less)'
    
def select_state_by_probs(states, probs):
    if len(states) == 1:
        return states[0]

    r = random.random()
    i = 0
    prob_sum = probs[0]
    while prob_sum < r:
        i += 1
        prob_sum += probs[i]
    return states[i]
    
if __name__ == "__main__":
    #Get ais from command line arguments
    if len(sys.argv) <= 2:
        print_usage()

    #Set up the board
    board = risktools.loadBoard("world.zip")
    
    #Keep all of the player access to ais
    ai_players = dict()
    time_left = dict()
    
    logname = 'matches\RISKMATCH'
    
    action_limit = 5000 #total between players
    player_time_limit = 600 #seconds per player
    
    #Load the ai's that were passed in
    for i in range(1,len(sys.argv),2):
        gai = imp.new_module("ai")
        filecode = open(sys.argv[i])
        exec filecode in gai.__dict__
        filecode.close()
        
        ai_file = os.path.basename(sys.argv[i])
        ai_file = ai_file[0:-3]
        logname = logname + '_' + ai_file + '_' + sys.argv[i+1]
      
        #Make new player
        ai_players[sys.argv[i+1]] = gai
        time_left[sys.argv[i+1]] = player_time_limit
        
        ap = risktools.RiskPlayer(sys.argv[i+1], len(board.players), 0, False)
        board.add_player(ap)
        
    #Get initial game state
    state = risktools.getInitialState(board)
    
    
    action_count = 0
    done = False
    
    timestr = time.strftime("%Y%m%d-%H%M%S")
    #Open the logfile
    logname = logname + '_' + timestr + '.log'
    logfile = open(logname, 'w')
    
    logfile.write(board.to_string())
    logfile.write('\n')
    
    final_string = ''
    
    #Play the game
    while not done:
        print '--*TURN', action_count, 'BEGIN*--'
        print 'CURRENT PLAYER: ', state.players[state.current_player].name
        print 'TURN-TYPE: ', state.turn_type
        print 'TIME-LEFT: ', time_left[state.players[state.current_player].name]
        
        #Log the current state
        logfile.write(state.to_string())
        logfile.write('\n')
        
        #Get current player
        current_ai = ai_players[state.players[state.current_player].name]
        
        #Make a copy of the state to pass to the other player
        ai_state = state.copy_state()
        
        #Start timer
        start_action = time.clock()
        
        #Ask the current player what to do
        current_action = current_ai.getAction(ai_state, time_left[state.players[state.current_player].name])
        current_player_name = state.players[state.current_player].name
        
        #Stop timer
        end_action = time.clock()
        
        #Determine time taken and deduct from player's time left
        action_length = end_action - start_action
        time_left[state.players[state.current_player].name] = time_left[state.players[state.current_player].name] - action_length
        current_time_left = time_left[state.players[state.current_player].name]
       
        print 'IN ', action_length, ' SECONDS CHOSE ACTION: ', current_action.description()
        
        #Execute the action on the master game state
        new_states, new_state_probabilities = risktools.simulateAction(state, current_action)
  
        #See if there is randomness in which state we go to next
        if len(new_states) > 1:
            #Randomly pick one according to probabilities
            state = select_state_by_probs(new_states, new_state_probabilities)
        else:
            state = new_states[0]

        logfile.write(current_action.to_string())
        logfile.write('\n')
        
        if state.turn_type == 'GameOver' or action_count > action_limit or current_time_left < 0:
            done = True
            #Get other player name
            other_player_name = ""
            for p in state.players:
                if p.name != current_player_name:
                    other_player_name = p.name
                    break
                    
            if state.turn_type == 'GameOver':
                print 'Game is over.', current_player_name, ' is the winner.'
                final_string = "RISKRESULT|" + current_player_name + ",1|" + other_player_name + ",0|Game End"
            if action_count > action_limit:
                print 'Action limit exceeded.  Game ends in a tie'
                final_string = "RISKRESULT|" + current_player_name + ",0.5|" + other_player_name + ",0.5|Action Limit Reached"
            if current_time_left < 0:
                print 'Agent time limit exceeded. ', current_player_name, ' loses by time-out.'
                final_string = "RISKRESULT|" + current_player_name + ",0|" + other_player_name + ",1|Time Out"
                
        action_count = action_count + 1
        print '--*TURN END*--'
        
    print 'GAME IS OVER! Final State at end of game:'
    state.print_state()
    print final_string
    logfile.write(state.to_string())
    logfile.write('\n')
    logfile.write(final_string)
    logfile.write('\n')
    
    logfile.close()