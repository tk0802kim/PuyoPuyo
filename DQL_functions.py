import numpy as np
import math

#game state includes: state, current block, next block.
#this is used to reduce the memory needed for memorylane
class gamestate:
    def __init__(self,game):
        self.state = game.state
        self.current_block = game.current_block
        self.next_block = game.next_block

#generates a view of the game available to the agent
#for 2 blocks: n blocks = game_n_color*(game_n_color+1)/2
#[0:n blocks-1] = current block, [n blocks,2*n blocks -1] = next block,
#[2*n blocks:2*n blocks+gamestate.state.size-1] = empty slot. [102:173] = red slot, etc
#total length = n_blocks*2+game_n_color*nrow*ncol
#indexs from topmost row with a puyo 
def agent_view(gamestate, game_n_color, hide_top_row=False):
    
    if gamestate.current_block.size>1:
        raise Exception('Haven\'t coded for nblock != 1 yet!' )
    
    nrow = gamestate.state.shape[0]-hide_top_row
    ncol = gamestate.state.shape[1]
    
    #get flipstate(viewstate flipped(so the top comes first in index), topstate(first nonzero row) and top_i(index of the top row))
    top_i = 0
    for i in range(nrow-1,-1,-1): #omit 13th row because thats invisible
            if np.any(gamestate.state[i,:]):
                flipstate = np.flip(gamestate.state[0:i+1,:],0).flatten()
                topstate = gamestate.state[i,:]
                top_i = i
                break
    
    #%%
    """
    recolor
        1 is the most numerous, 2 is next.....
    rules:
        1. Most puyo color in viewspace
        2. color of current puyo (multiply 0.5 to count so you dont flip the previous results )
        3. color of next puyo (multiply 0.25 to count)
        4. more in first row, second row, third row....
        5. check middle in first row, next ones...second row middle, next.....
       
    This fails only if:
        1. same number of placed puyo
        2. not favored by cur or next blocks
        3. symmetric about middle
    """
    viewspace = gamestate.state[0:nrow,:]
    recolored = np.zeros((nrow,ncol),dtype=int)
    rc_cur = np.zeros(gamestate.current_block.shape,dtype=int)
    rc_next = np.zeros(gamestate.next_block.shape,dtype=int)
    
    tiebreaker_level = 1
    p_i=pair_ind(ncol) #gives back indexes of the middle pieces of a row, and moving outward
    
    color_sum = np.array([np.count_nonzero(viewspace==c) for c in range(1,game_n_color+1)],dtype=float) #rule 1
    if len(np.unique(color_sum)) != game_n_color:
        cur_sum = np.array([np.count_nonzero(gamestate.current_block==c) for c in range(1,game_n_color+1)],dtype=float) #rule 2
        color_sum += (1/2**tiebreaker_level)*cur_sum
        
        if len(np.unique(color_sum)) != game_n_color:
            tiebreaker_level += 1
            next_sum = np.array([np.count_nonzero(gamestate.current_block==c) for c in range(1,game_n_color+1)],dtype=float) #rule 3
            color_sum += (1/2**tiebreaker_level)*next_sum
            
            if len(np.unique(color_sum)) != game_n_color:                
                for i in range(top_i,-1,-1):
                    tiebreaker_level += 1
                    color_sum += (1/2**tiebreaker_level)*np.array([np.count_nonzero(viewspace[i,:]==c) for c in range(1,game_n_color+1)],dtype=float) #rule 4

                if len(np.unique(color_sum)) != game_n_color:                    
                    for i in range(top_i,-1,-1):
                        for inds in p_i:
                            tiebreaker_level += 1
                            color_sum += (1/2**tiebreaker_level)*np.array([np.count_nonzero(viewspace[i,inds]==c) for c in range(1,game_n_color+1)],dtype=float) #rule 5
    
    recolor_ind = np.flip(np.argsort(color_sum))+1
    color_sum_recolored = np.flip(np.sort(color_sum))
    #rc is the original color, c is the new color. So the state is going form rc->c
    for rc, c in enumerate(recolor_ind):
        recolored += (rc+1)*(viewspace==c)           #recolored gamespace
        rc_cur += (rc+1)*(gamestate.current_block==c) #recolored cur block
        rc_next += (rc+1)*(gamestate.next_block==c)   #recolored next block
    
    """
    once order is decided, check outermost in first row, higher rank should be left
        
    if there are still ties
    find lowest ranking duplicates
    with the non-duplicates, flip to right order
    then, the left most duplicates are higher ranks
    
    start here
    """
    done = 0
    for ti in range(top_i,-1,-1): #iterate from the top most occupied state to the bottom
        for inds in reversed(p_i): #iterate from outermost
            if inds.shape[0] == 1:
                break            
            ts = recolored[ti,:] #row being looked at now
            o_l,o_r = ts[inds[0]],ts[inds[1]]
            
            if color_sum_recolored[o_l-1] > color_sum_recolored[o_r-1]:
                done = 1
                break
            elif color_sum_recolored[o_l-1] < color_sum_recolored[o_r-1]:
                recolored = np.flip(recolored, axis=1)
        if done==1:
            break

   
   
    #%%
    
    """this is coded for only 1 block stuff"""
    # n_orientation = ncol
    n_blocks = game_n_color #number of different blocks that can be given
    
    
    """following can be universal"""
    viewstate = np.zeros(n_blocks*2+(game_n_color+1)*nrow*ncol,dtype=np.int) #this assumes no garbage puyo's with game_n_color+1
    
    cur_block_i = block_ind(rc_cur)
    next_block_i = block_ind(rc_next)
    
    viewstate[cur_block_i-1] = 1
    viewstate[next_block_i-1+n_blocks] = 1
    
    for ii in range(game_n_color+1):
        counter=0
        for i in range(top_i-1,-1,-1): #omit 13th row because thats invisible

            topstate = gamestate.state[i,:];
            
            if not any(topstate):
                raise('issue with viewstate')
                  
            # for slot in topstate:
            start = n_blocks*2+ii*nrow*ncol+ncol*counter
            end = n_blocks*2+ii*nrow*ncol+ncol*(counter+1)
            try:
                viewstate[start:end] = (topstate==ii)*1
            except:
                print('meh')   

            counter+=1                           
    return viewstate
    
#find block index that correstponds to the given block
def block_ind(block):
    return block
    #this is 2block stuff
    # block_list = np.array([[1,1],[1,2],[1,3],[1,4],[1,5],[2,2],[2,3],[2,4],[2,5],[3,3],[3,4],[3,5],[4,4],[4,5],[5,5]])
    # for i in range(15):
    #         if np.array_equal(block_list[i],block):
    #             return i
    # raise Exception('block not found')

#memory includes starting game state, action and reward of that action, and the resulting gamestate
class memory:
    def __init__(self, cur_gs, action, reward, next_gs):
        self.cur_gs = cur_gs
        self.action = action
        self.reward = reward
        self.next_gs = next_gs
        
#sets the reward map    
def rewardmap(score):
    return np.log(score+1)



def pair_ind(nrow): #gives back indexes of the middle pieces of a row, and moving outward
    ind_list = []
    if nrow%2 == 1:
        ind_list.append(np.array([nrow//2]))
        for i in range(1,nrow//2+1):
             ind_list.append(np.array([nrow//2-i,nrow//2+i]))       
             
    elif nrow%2 == 0:
        ind_list.append(np.array([int(nrow/2-1),int(nrow/2)]))
        for i in range(1,int(nrow/2)):
             ind_list.append(np.array([ind_list[0][0]-i,ind_list[0][1]+i]))  
             
    else:
         raise Exception('Issue in DQL_functions/pair_ind' )   

    return ind_list
