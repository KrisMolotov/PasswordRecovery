import hashlib
import argparse
from enum import Enum
import multiprocessing as mp
import time


class Encoding(Enum):
    utf8 = 'utf-8'
    ascii = 'ascii'
    utf16be = 'utf-16-be'
    utf16le = 'utf-16-le'

    def str(self):
        return self.value


class HashFunctions(Enum):
    md4 = 'md4'
    md5 = 'md5'
    sha256 = 'sha256'
    sha1 = 'sha1'
    sha512 = 'sha512'

    def str(self):
        return self.value

    def get_hash_object(self):
        return hashlib.new(self.value)


processes = mp.cpu_count()


def createParser():
    prs = argparse.ArgumentParser()
    prs.add_argument('--wordlist', type=str)
    prs.add_argument('-e', '--encoding', type=Encoding, default=Encoding.ascii)
    prs.add_argument('-f', '--function', type=HashFunctions, default=HashFunctions.md5)
    prs.add_argument('--hashlist', type=str)
    return prs


parser = createParser()
args = parser.parse_args()
wordlist_file = args.wordlist
encoding = args.encoding.value
hash_function_name = args.function
hashlist_file = args.hashlist


def create_hash(hash_line):
    hash_object = hash_function_name.get_hash_object()
    hash_object.update(hash_line.encode(encoding=encoding))
    return hash_object.hexdigest()


def comparison_of_words(passwords, part_of_wordlist):
    extra = dict()
    for i in part_of_wordlist:
        hashed_line = create_hash(i)
        coincidence = list()
        for password in passwords:
            if password == hashed_line:
                coincidence.append(password)
        if len(coincidence) != 0:
            extra[i] = coincidence
    return extra


passwords_for_processing = None


def pool_initializer(hashes):
    global passwords_for_processing
    passwords_for_processing = hashes


def comparison_caller(part_of_wordlist):
    dictionary = comparison_of_words(passwords_for_processing, part_of_wordlist)
    return dictionary


if __name__ == '__main__':
    with open(wordlist_file, 'r') as wordlist, open(hashlist_file, 'r') as hashlist:
        word_list = wordlist.readlines()
        hash_list = hashlist.readlines()
        size_part_for_handling = len(hash_list) / processes
        size_part_for_handling = int(size_part_for_handling)
        word_list = [word.rstrip('\n') for word in word_list]
        hash_list = [el.rstrip('\n') for el in hash_list]
        if size_part_for_handling == 0:
            size_part_for_handling += 1
        parts = [word_list[i: i + size_part_for_handling] for i in range(0, len(word_list), size_part_for_handling)]
        thread = mp.Pool(processes, initializer=pool_initializer, initargs=(hash_list,))
        final_list = []
        t_start = time.perf_counter()
        for i in parts:
            intermediate_list = thread.apply_async(comparison_caller, (i,))
            final_list.append(intermediate_list)
        thread.close()
        thread.join()
        for item in final_list:
            print(item.get())
        all_time = time.perf_counter() - t_start
        print(f"Summary time of calculation is {all_time} seconds")
