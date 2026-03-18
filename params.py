# coding=utf-8


class ALFEParams:

    # Markets

    MARKET_SZ = 0  # Shenzhen
    MARKET_SH = 1  # Shanghai

    # K-line types
    # 0 -   5 min K-line
    # 1 -   15 min K-line
    # 2 -   30 min K-line
    # 3 -   1 hour K-line
    # 4 -   Daily K-line
    # 5 -   Weekly K-line
    # 6 -   Monthly K-line
    # 7 -   1 min (extended)
    # 8 -   1 min K-line
    # 9 -   Daily K-line
    # 10 -  Quarterly K-line
    # 11 -  Yearly K-line

    KLINE_TYPE_5MIN = 0
    KLINE_TYPE_15MIN = 1
    KLINE_TYPE_30MIN = 2
    KLINE_TYPE_1HOUR = 3
    KLINE_TYPE_DAILY = 4
    KLINE_TYPE_WEEKLY = 5
    KLINE_TYPE_MONTHLY = 6
    KLINE_TYPE_EXHQ_1MIN = 7
    KLINE_TYPE_1MIN = 8
    KLINE_TYPE_RI_K = 9
    KLINE_TYPE_3MONTH = 10
    KLINE_TYPE_YEARLY = 11


    # ref : https://github.com/alpha-evolver/alfe/issues/7
    # Max 2000 tick quotes
    MAX_TRANSACTION_COUNT = 2000
    # Max 800 K-line data points
    MAX_KLINE_COUNT = 800


    # Block related parameters
    BLOCK_SZ = "block_zs.dat"
    BLOCK_FG = "block_fg.dat"
    BLOCK_GN = "block_gn.dat"
    BLOCK_DEFAULT = "block.dat"
