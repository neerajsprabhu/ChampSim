#ifndef BTB_H
#define BTB_H

// BTB
class BRANCH_TARGET_PRED
{
private:
    // BTB common structure
    struct BTB_entry {
        uint64_t tag;
        int64_t offset;
        uint64_t lru;
    };

    struct BTB_XC_entry {
        uint64_t tag;
        uint64_t target;
    };

    // parameters
    static const int BTB_NWAY = 8;
    static const int BTB_NSET = 256;
    static const int BTB_NSET_XC = 32;
    static const int RAS_SIZE = 64;
    static const uint32_t BTB_OFFSET = 0;
    static const uint32_t BTB_SET_MASK = (1 << 11) - 1;

    uint64_t lru_counter;

    // branch history
    uint64_t btb_ghr[16];

    // BTB structures
    BTB_entry btb[BTB_NSET][BTB_NWAY];
    BTB_XC_entry btb_xc[BTB_NSET_XC];


    // return stack
    uint64_t ras[RAS_SIZE], ras_size, ras_top;

    // indirect predictor access
    uint64_t ittage_predict(uint64_t ip, uint64_t target);
    void ittage_update(BTB_entry& hit_entry, uint64_t target, bool mispred);

public:
    // snoop return stack
    uint64_t predict_ras(uint64_t target) { return (ras_size > 0) ? ras[ras_top] : target; }

    // make target prediction
    uint8_t predict_target(uint64_t ip, uint8_t type, uint64_t &target);

    // update / initialize predictor
    void    update_target(uint64_t ip, uint8_t type, uint64_t target);
    void    update_history(uint64_t ip, uint8_t type, uint64_t target);
    void    initialize();
    void    access_btb(){lru_counter++;}
};

#endif
