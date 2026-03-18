#coding: utf-8

from alfe.reader.base_reader import BaseReader
from alfe.crawler.history_financial_crawler import HistoryFinancialCrawler

# Use HistoryFinancialCrawler in history_financial_crawler to complete this function, this reader only provides simple wrapper

class HistoryFinancialReader(BaseReader):

    def get_df(self, data_file):
        """
        Read historical financial data file, and return pandas result, format like gpcw20171231.zip, for specific field meanings refer to

        https://github.com/alpha-evolver/alfe/issues/133

        :param data_file: Data file path, data file type can be .zip file, or extracted .dat
        :return: pandas DataFrame format historical financial data
        """

        crawler = HistoryFinancialCrawler()

        with open(data_file, 'rb') as df:
            data = crawler.parse(download_file=df)

        return crawler.to_df(data)


if __name__ == '__main__':
    # print(HistoryFinancialReader().get_df('/tmp/tmpfile.zip'))
    print(HistoryFinancialReader().get_df('/tmp/gpcw20170930.dat'))
