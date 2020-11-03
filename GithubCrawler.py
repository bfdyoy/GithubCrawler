import argparse
import requests
import json
import configparser
from distutils.util import strtobool
from git import Repo


class Crawler:
    __url = 'https://api.github.com/search/repositories?q=stars:%3E=100+size:%3C=1000000+mirror:false+fork:' \
            'false+language:cpp&sort=stars&order=desc&per_page=100&page=1'

    def __init__(self):
        self.__make_repo_list = False
        self.__do_clone = False
        self.__max_repos = False
        self.__list_file_name = ""
        self.__clone_directory = ""
        self.__user = ""
        self.__token = ""

    def __setup_url(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(url, headers=headers, auth=(self.__user, self.__token))
        try:
            return response
        except:
            response.raise_for_status()

    def __setup_config(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--config",
                            help="config file path",
                            default='crawler.conf',
                            type=str)
        args = parser.parse_args()

        config = configparser.ConfigParser()
        config.read(args.config)

        self.__make_repo_list = bool(config['crawler']['make_repo_list'])
        self.__list_file_name = config['crawler']['list_file']
        self.__do_clone = bool(config['crawler']['do_clone'])
        self.__clone_directory = config['crawler']['clone_directory']
        self.__max_repos = int(config['crawler']['max_repos'])
        self.__user = config['crawler']['username']
        self.__token = config['crawler']['token']

    def find_projects(self):
        self.__setup_config()

        response = self.__setup_url(self.__url)

        result = json.loads(response.content.decode('utf-8'))

        if self.__make_repo_list and self.__list_file_name:
            with open(self.__list_file_name, 'w') as of:
                counter = 0

                print('Total number of projects found: ' + str(result['total_count']))

                while 'next' in response.links and counter <= self.__max_repos:

                    for repo in result['items']:
                        if counter <= self.__max_repos:
                            counter += 1
                            of.write(repo['full_name'] + '\n')

                            if self.__do_clone:
                                print('Clone repository "' + repo['full_name'] + '" ...')
                                Repo.clone_from(repo['clone_url'], self.__clone_directory + '/' +
                                                repo['full_name'])
                                print('Done')

                    url = response.links['next']['url']
                    response = self.__setup_url(url)
                    result = json.loads(response.content.decode('utf-8'))
