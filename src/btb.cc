#include "ooo_cpu.h"
#include "btb.h"
#include "set.h"
#include <cmath>

// initialize the predictor
void BRANCH_TARGET_PRED::initialize()
{
    lru_counter=0;
    for(uint64_t j=0; j<BTB_NSET; j++){
        for(uint64_t i=0; i<BTB_NWAY; i++){
            btb[j][i].tag=0;
            btb[j][i].offset=0;
            btb[j][i].lru=0;
        }
    }
    for(uint64_t i=0; i<BTB_NSET_XC; i++)
    {
        btb_xc[i].tag=0;
        btb_xc[i].target=0;
    }
    // initialize branch target predictor
    // double alpha = pow((double)MAX_HIST / (double)MfIN_HIST, 1.0 / (ITTAGE_NTAB-1));
    // for(int i=0; i<ITTAGE_NTAB; i++)
    // {
    //     ittage_hlen[i] = (int)((MIN_HIST * pow(alpha, i)) + 0.5);
    // }
}

// make target prediction
uint8_t BRANCH_TARGET_PRED::predict_target(uint64_t ip, uint8_t type, uint64_t &target)
{
    access_btb();
    uint64_t btb_idx = (ip >> BTB_OFFSET) & (BTB_NSET-1);
    uint64_t btb_tag = ip;
    uint64_t btb_way = 0;


    for(btb_way=0; btb_way<BTB_NWAY; btb_way++)
    {
        BTB_entry& entry = btb[btb_idx][btb_way];
        if(entry.tag == btb_tag)
        {
            target = entry.offset + ip;
            entry.lru=lru_counter;
            if((ras_size > 0) && (type == BRANCH_RETURN)) target = ras[ras_top];
            return 2;
        }
    }

    BTB_XC_entry& entry = btb_xc[btb_idx];
    if(entry.tag == btb_tag)
    {
        target = entry.target;
        if((ras_size > 0) && (type == BRANCH_RETURN)) target = ras[ras_top];
        return 2;
    }


    // BTB miss
    return 0;
}

// update branch predictor
void BRANCH_TARGET_PRED::update_target(uint64_t ip, uint8_t type, uint64_t target)
{
    access_btb();
    uint64_t btb_idx = (ip >> BTB_OFFSET) & (BTB_NSET-1);
    uint64_t btb_tag = ip;
    uint64_t btb_way = 0;
    uint64_t vic_way = 0;
    int64_t offset=target-ip;
    int nbits=(int)(log2(offset)-1);
    int minway;
    uint64_t minlru=lru_counter;
    bool check_xc=false;
    
    if(type == BRANCH_RETURN) minway=0;
    else if (nbits>0) minway=1;
    else if (nbits>4) minway=2;
    else if (nbits>5) minway=3;
    else if (nbits>7) minway=4;
    else if (nbits>9) minway=5;
    else if (nbits>11) minway=6;
    else if (nbits>19) minway=7;
    else if (nbits>25) check_xc=true;

    if(!check_xc)
    {
        bool btb_hit = false;
        for(btb_way=0; btb_way<BTB_NWAY; btb_way++)
        {
            BTB_entry& entry = btb[btb_idx][btb_way];
            if(entry.tag == btb_tag)
            {
                btb_hit = true;
                break;
            }
        }

        if(!btb_hit)
        {
            for(btb_way=BTB_NWAY; btb_way>minway; btb_way--)
            {
                BTB_entry& entry = btb[btb_idx][btb_way];
                if(minlru<entry.lru){
                    minlru=entry.lru;
                    vic_way=btb_way;
                }
            }
            BTB_entry& vic_entry = btb[btb_idx][vic_way];

            vic_entry.tag = btb_tag;
            vic_entry.offset = offset;
            vic_entry.lru=lru_counter;
        }
        else // BTB hit
        {
            BTB_entry& hit_entry = btb[btb_idx][btb_way];
            hit_entry.offset=target-ip;
            hit_entry.lru=lru_counter;
        }
    }
    else
    {
        BTB_XC_entry& entry=btb_xc[btb_idx];
        entry.tag=btb_tag;
        entry.target=target;
    }
}


// update branch predictor history
void BRANCH_TARGET_PRED::update_history(uint64_t ip, uint8_t type, uint64_t target)
{
    // branch target history hash computation
    uint64_t hash = (target >> 2) & 0xffULL ;
    for(int i=0; i<16; i=i+1) // 16 * 32 = 512-bit total
    {
        btb_ghr[i] <<= 2;
        btb_ghr[i] ^= hash;
        hash = (btb_ghr[i] >> 32) & 3;
    }

    // return stack maintenance
    if((type == BRANCH_DIRECT_CALL) || (type == BRANCH_INDIRECT_CALL))
    {
        if(ras_size < RAS_SIZE) ras_size++;
        ras_top = (ras_top + 1) & (RAS_SIZE - 1);
        ras[ras_top] = ip + 4;
    }
    else if(type == BRANCH_RETURN)
    {
        if(ras_size > 0) ras_size--;
        ras_top = (ras_top + RAS_SIZE - 1) & (RAS_SIZE - 1);
    }
    else if((ras_size > 0) && (ras[ras_top]==target))
    {
        if(ras_size > 0) ras_size--;
        ras_top = (ras_top + RAS_SIZE - 1) & (RAS_SIZE - 1);
    }
}
