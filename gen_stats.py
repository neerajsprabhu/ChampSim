#import matplotlib.pyplot as plt
#import numpy as np
import os
import csv
import multiprocessing

def func1(x):
    cmd="./run_champsim.sh hashed_perceptron-fdip1-no-no-no-lru-1core 50 50 ../../traces/CVP1/srv"+str(x)+".champsim.xz"
    print(cmd)
    os.system(cmd)

if __name__=="__main__":
    for j in range(20):
        processes = []
        for i in range(16):
            p = multiprocessing.Process(target=func1, args=(16*j+i,))
            processes.append(p)
            p.start()

        for process in processes:
            process.join()
    


    srv=[]
    ipc=[]
    btb_loads=[]
    btb_stores=[]
    btb_lmisses=[]
    btb_smisses=[]
    for i in range(1,320):
        f=open('/home/neeraj/BTP/traces/CVP1/srv'+str(i)+'.champsim.xz-hashed_perceptron-fdip1-no-no-no-lru-1core.txt', 'r')
        a=f.readlines()
        for j in range(len(a)):
            words=a[j].split()
            # print(words)
            if(words[0:4]==['CPU', '0', 'cumulative', 'IPC:']):
                ipc.append(float(words[4]))
                srv.append(i)
                #print(float(words[4]))
            if(words[0:2]==['BTB','Loads:']):
                btb_loads.append(int(words[2]))
                btb_lmisses.append(int(words[6]))
                #print(int(words[2]))
                #print(int(words[6]))
            if(words[0:2]==['BTB','Stores:']):
                btb_stores.append(int(words[2]))
                btb_smisses.append(int(words[6]))
                #print(int(words[2]))
                #print(int(words[6]))
    # print(ipc)
    # print(srv)
    # print(btb_lmisses)
    # print(btb_smisses)
    # print(btb_loads)
    # print(btb_stores)
    fields=['Trace','IPC','Loads','Stores','Load Misses','Store Misses']
    filename="Stats_512.csv"
    #print(ipc)
    #print(btb_loads)
    #print(btb_stores)
    #print(btb_lmisses)
    #print(btb_smisses)
    with open(filename,'w') as csvfile:
        csvwriter=csv.writer(csvfile)
        csvwriter.writerow(fields)
        for i in range(len(ipc)):
            #print(i)
            csvwriter.writerow([srv[i],ipc[i],btb_loads[i],btb_stores[i],btb_lmisses[i],btb_smisses[i]])
