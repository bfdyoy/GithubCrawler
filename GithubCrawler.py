import argparse
import requests
import json
import configparser
from distutils.util import strtobool
import sys
from tqdm import tqdm
import os
from git import Repo
import zipfile
import glob


class Crawler:
    __url = 'https://api.github.com/search/repositories?q=stars:%3E=100+size:%3C=400000+mirror:false+fork:' \
            'false+language:cpp&sort=stars&order=desc&per_page=100&page=1'

    def __init__(self):
        self.__make_repo_list = False
        self.__do_clone = False
        self.__max_repos = False
        self.__do_download = False
        self.__list_file_name = ""
        self.__clone_directory = ""
        self.__user = ""
        self.__token = ""
        self.__zip_directory_name = ""
        self.__unzip_directory = ""

    def __setup_url(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(url, headers=headers, auth=(self.__user, self.__token))
        if response.ok:
            return response
        else:
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

        self.__make_repo_list = bool(strtobool(config['crawler']['make_repo_list']))
        self.__max_repos = int(config['crawler']['max_repos'])
        self.__user = config['crawler']['username']
        self.__token = config['crawler']['token']
        self.__do_download = config['crawler']['download_zip']
        self.__do_clone = bool(strtobool(config['crawler']['do_clone']))

        self.__list_file_name = config['data_extraction']['list_file']
        self.__clone_directory = config['data_extraction']['clone_directory']
        self.__zip_directory_name = config['data_extraction']['zip_file']
        self.__unzip_directory = config['data_extraction']['unzip_file']

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
                            size += int(repo['size']) / 1000
                            if self.__do_clone:
                                print('Clone repository "' + repo['full_name'] + '" ...')
                                Repo.clone_from(repo['clone_url'], self.__clone_directory + '/' + repo['full_name'])
                                print('Done')

                        if self.__do_download and self.__zip_directory_name:
                            print('Download repository "' + repo['full_name'] + '" as zip ...')

                            zip_url = 'https://github.com/' + repo['full_name'] + '/archive/master.zip'
                            zip_response = requests.get(zip_url, stream=True)

                            if not os.path.exists(self.__zip_directory_name + '/' + repo['full_name'].split('/')[0]):
                                os.makedirs(self.__zip_directory_name + '/' + repo['full_name'].split('/')[0])

                            with open(self.__zip_directory_name + '/' + repo['full_name'] + '.zip', 'wb') as handle:
                                for data in tqdm(zip_response.iter_content()):
                                    handle.write(data)

                    url = response.links['next']['url']
                    response = self.__setup_url(url)
                    result = json.loads(response.content.decode('utf-8'))

    def unzip_files(self):
        self.__setup_config()
        folders_list = []
        zip_directory = str(self.__zip_directory_name)
        with open(self.__list_file_name, 'r') as list_of:
            for line in list_of:
                splitted_line = line.strip().split('/')
                folders_list.append(splitted_line[0])

        folders_list = list(dict.fromkeys(folders_list))
        dataset_path = os.path.dirname(__file__) + '/' + self.__unzip_directory
        for folder in folders_list:
            zip_full_path = os.path.dirname(__file__) + '/' + zip_directory + '/' + folder + '/' + '*.zip'
            for name in glob.glob(zip_full_path):
                try:
                    with zipfile.ZipFile(name, 'r') as zip_ref:
                        zip_ref.extractall(dataset_path)
                except(zipfile.BadZipfile):
                    print("Bad zip file " + name)
