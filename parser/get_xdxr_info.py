# coding=utf-8

from alfe.parser.base import BaseParser
from alfe.helper import get_datetime, get_volume, get_price, get_time
from collections import OrderedDict
import struct
import six
"""
need to fix

get_volume ?

4098 ---> 3.0

2434.0062499046326 ---> 2.6

1218.0031249523163 ---> 2.3

"""
"""

        1 Ex-rights/Ex-dividend 002175 2008-05-29
        2 Bonus/Rights Issue Listing  000656 2015-04-29
        3 Non-tradable Shares Listing 000656 2010-02-10
        4 Unknown Share Capital Change 600642 1993-07-19
        5 Share Capital Change 000656 2017-06-30
        6 New Share Issue 600887 2002-08-20
        7 Share Buyback  600619 2000-09-08
        8 New Share Issue Listing 600186 2001-02-14
        9 Rights Transfer Listing 600811 2017-07-25
        10 Convertible Bond Listing 600418 2006-07-07
        11 Share Expansion/Contraction  600381 2014-06-27
        12 Non-tradable Share Contraction 600339 2006-04-10
        13 Subscription Warrant Issue 600008 2006-04-19
        14 Put Warrant Issue 000932 2006-03-01

"""


XDXR_CATEGORY_MAPPING = {
    1 : "Ex-rights/Ex-dividend",
    2 : "Bonus/Rights Issue Listing",
    3 : "Non-tradable Shares Listing",
    4 : "Unknown Share Capital Change",
    5 : "Share Capital Change",
    6 : "New Share Issue",
    7 : "Share Buyback",
    8 : "New Share Issue Listing",
    9 : "Rights Transfer Listing",
    10 : "Convertible Bond Listing",
    11 : "Share Expansion/Contraction",
    12 : "Non-tradable Share Contraction",
    13 : "Subscription Warrant Issue",
    14 : "Put Warrant Issue"
}


class GetXdXrInfo(BaseParser):

    def setParams(self, market, code):
        if type(code) is six.text_type:
            code = code.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 1f 18 76 00 01 0b 00 0b 00 0f 00 01 00')
        pkg.extend(struct.pack("<B6s", market, code))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0

        if len(body_buf) < 11:
            return []

        pos += 9 # skip 9
        (num, ) = struct.unpack("<H", body_buf[pos:pos+2])
        pos += 2

        rows = []

        def _get_v(v):
            if v == 0:
                return 0
            else:
                return get_volume(v)

        for i in range(num):
            market, code = struct.unpack(u"<B6s", body_buf[:7])
            pos += 7
            # noused = struct.unpack(u"<B", body_buf[pos: pos+1])
            pos += 1 #skip a byte
            year, month, day, hour, minite, pos = get_datetime(9, body_buf, pos)
            (category, ) = struct.unpack(u"<B", body_buf[pos: pos+1])
            pos += 1



            # b'\x00\xe8\x00G' => 33000.00000
            # b'\x00\xc0\x0fF' => 9200.00000
            # b'\x00@\x83E' => 4200.0000

            suogu = None
            panqianliutong, panhouliutong, qianzongguben, houzongguben = None, None, None, None
            songzhuangu, fenhong, peigu, peigujia = None, None, None, None
            fenshu, xingquanjia = None, None
            if category == 1:
                fenhong, peigujia, songzhuangu, peigu  = struct.unpack("<ffff", body_buf[pos: pos + 16])
            elif category in [11, 12]:
                (_, _, suogu, _) = struct.unpack("<IIfI", body_buf[pos: pos + 16])
            elif category in [13, 14]:
                xingquanjia, _, fenshu, _ = struct.unpack("<fIfI", body_buf[pos: pos + 16])
            else:
                panqianliutong_raw, qianzongguben_raw, panhouliutong_raw, houzongguben_raw = struct.unpack("<IIII", body_buf[pos: pos + 16])
                panqianliutong = _get_v(panqianliutong_raw)
                panhouliutong = _get_v(panhouliutong_raw)
                qianzongguben = _get_v(qianzongguben_raw)
                houzongguben = _get_v(houzongguben_raw)



            pos += 16

            row = OrderedDict(
                [
                    ('year', year),
                    ('month', month),
                    ('day', day),
                    ('category', category),
                    ('name', self.get_category_name(category)),
                    ('fenhong', fenhong),
                    ('peigujia', peigujia),
                    ('songzhuangu', songzhuangu),
                    ('peigu', peigu),
                    ('suogu', suogu),
                    ('panqianliutong', panqianliutong),
                    ('panhouliutong', panhouliutong),
                    ('qianzongguben', qianzongguben),
                    ('houzongguben', houzongguben),
                    ('fenshu', fenshu),
                    ('xingquanjia', xingquanjia)
                ]
            )
            rows.append(row)

        return rows

    def get_category_name(self, category_id):

        if category_id in XDXR_CATEGORY_MAPPING:
            return XDXR_CATEGORY_MAPPING[category_id]
        else:
            return str(category_id)




if __name__ == '__main__':

    from alfe.util.best_ip import select_best_ip
    from alfe.hq import AlfeHq_API
    api = AlfeHq_API()
    with api.connect():
        # 11 Share Expansion/Contraction
        print(api.to_df(api.get_xdxr_info(1, '600381')))
        # 12 Non-tradable Share Contraction
        #print(api.to_df(api.get_xdxr_info(1, '600339')))
        # 13 Subscription Warrant Issue
        #print(api.to_df(api.get_xdxr_info(1, '600008')))
        # 14 Put Warrant Issue
        #print(api.to_df(api.get_xdxr_info(0, '000932')))
