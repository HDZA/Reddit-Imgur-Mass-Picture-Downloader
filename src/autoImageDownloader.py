#Credit goes to /u/GoldenSights for showing me his post data collection script.


import datetime
import praw
import time
import traceback
from bs4 import BeautifulSoup
import requests
import re
from PIL import Image
import os
import sys
import warnings
warnings.filterwarnings("ignore")

USERAGENT = "I AM A SILLY IMAGE AUTOMATON by /u/TheEmperor"
# http://redd.it/3cm1p8
r = praw.Reddit(user_agent = USERAGENT)
totalNum= 0;
UNIX_TIME_IMGUR_CREATION = 1235347200 #Imgur wasn't launched until February 23, 2009. There's no point in doing any search queries before this time.

def get_all_posts(subreddit, lower=None, maxupper=None, tags_to_ignore = "",  interval=86400, usermode=False ):

    offset = -time.timezone

    if lower is "":
        if usermode is False:
            if not isinstance(subreddit, praw.objects.Subreddit):
                subreddits = subreddit.split('+')
                subreddits = [r.get_subreddit(sr) for sr in subreddits]
                creation = min([sr.created_utc for sr in subreddits])
            else:
                creation = subreddit.created_utc
        else:
            if not isinstance(usermode, praw.objects.Redditor):
                user = r.get_redditor(usermode)
            creation = user.created_utc
        if creation < UNIX_TIME_IMGUR_CREATION: #If the subreddit was created before Feb 23, 2009. There wont be any imgur posts to gather. Change the lower date to the date imgur was launched. 
            lower = UNIX_TIME_IMGUR_CREATION
        else:
            lower = creation

    if maxupper is "":
        nowstamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        maxupper = nowstamp

    lower -= offset
    maxupper -= offset
    upper = lower + interval
    itemcount = 0

    toomany_inarow = 0
    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower', human(lower), lower)
        print('Upper', human(upper), upper)
        while True:
            try:
                if usermode is not False:
                    query = '(and author:"%s" (and timestamp:%d..%d))' % (
                        usermode, lower, upper)
                else:
                    query = 'timestamp:%d..%d' % (lower, upper)
                searchresults = list(r.search(query, subreddit=subreddit,
                                              sort='new', limit=100,
                                              syntax='cloudsearch'))
                break
            except:
                traceback.print_exc()
                print('resuming in 5...')
                time.sleep(5)
                continue

        searchresults.reverse()
        print([i.id for i in searchresults])
        print()
        
        for i in searchresults:
            if("imgur" in i.url and len(tags_to_ignore) == 0): #If the user supplied an empty tag selection just run this check. 
                downloadImage(i.url,i, subreddit)
            elif("imgur" in i.url):
                split_title = i.title.split();
                if(tags_to_ignore in split_title): #If the title contains any words in the tags_to_ignore list then we skip it and don't bother downloading.
                    print(i.title + " contains words listed in the user's do not download tags")
                    continue

        itemsfound = len(searchresults)
        itemcount += itemsfound
        print('Found', itemsfound, 'items')
        if itemsfound < 75:
            print('Too few results, increasing interval', end='')
            diff = (1 - (itemsfound / 75)) + 1
            diff = min(2, diff)
            interval = int(interval * diff)
        if itemsfound > 99:
            print('Too many results, reducing interval', end='')
            interval = int(interval * (0.8 - (0.05*toomany_inarow)))
            upper = lower + interval
            toomany_inarow += 1
        else:
            #Intentionally not elif
            lower = upper
            upper = lower + interval
            toomany_inarow = max(0, toomany_inarow-1)

        print()



def human(timestamp):
    x = datetime.datetime.utcfromtimestamp(timestamp)
    x = datetime.datetime.strftime(x, "%b %d %Y %H:%M:%S")
    return x

def humannow():
    x = datetime.datetime.now(datetime.timezone.utc).timestamp()
    x = human(x)
    return x

def humanToUnix(givenDate):
    return time.mktime(datetime.datetime.strptime(givenDate, "%d/%m/%Y").timetuple()) #Assumes midnight in the given timezone, converts this to UTC time later on. 

def downloadImgurImage(imageUrl, localFileName):
    response = requests.get(imageUrl)
    if response.status_code == 200:
        print('Downloading %s...' % (localFileName))
        if '/' in localFileName:
            print("This is the file name I was going to use: ", localFileName)
            localFileName = localFileName.replace('/', '')
        with open(localFileName, 'wb') as fo:
            for chunk in response.iter_content(4096):
                fo.write(chunk)
    global totalNum
    totalNum+=1
    print("So far " ,totalNum, " of images have been downloaded")
    


def downloadImage(url,submission, targetSubreddit):
    imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')
    
    print("Attempting to download image at: ", url)
    
#    htmlSource = requests.get(url).text
    if 'http://imgur.com/a/' in url:
        # This is an album submission.
        albumId = submission.url[len('http://imgur.com/a/'):]
        htmlSource = requests.get(submission.url)
        if htmlSource.status_code ==404:
            print("This image or collection of images no longer exist!")
            return
        soup = BeautifulSoup(htmlSource.text, "lxml")
        matches = soup.select('.album-view-image-link a')
        for match in matches:
            imageUrl = match['href']
            if '?' in imageUrl:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
            else:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:]
            localFileName = 'reddit_%s_%s_album_%s_imgur_%s' % (targetSubreddit, submission.id, albumId, imageFile)
            downloadImgurImage('http:' + match['href'], localFileName)


    elif 'http://i.imgur.com/' in url:
        # The URL is a direct link to the image.
        htmlSource = requests.get(submission.url)
        if htmlSource.status_code ==404:
            print("This image or collection of images no longer exist!")
            return
        mo = imgurUrlPattern.search(url) # using regex here instead of BeautifulSoup because we are pasing a url, not html

        imgurFilename = mo.group(2)
        if '?' in imgurFilename:
            # The regex doesn't catch a "?" at the end of the filename, so we remove it here.
            imgurFilename = imgurFilename[:imgurFilename.find('?')]

        localFileName = 'reddit_%s_%s_album_None_imgur_%s' % (targetSubreddit, submission.id, imgurFilename)
        downloadImgurImage(submission.url, localFileName)


    elif 'http://imgur.com/' in url:
        # This is an Imgur page with a single image.
        htmlSource = requests.get(submission.url)
        if htmlSource.status_code == 200:
            if htmlSource.history and htmlSource.url != url:
                print("The request was redirected, it must be an older link")
                print("This is the link as it stands now. ", htmlSource.url)
                downloadImage(htmlSource.url,submission,targetSubreddit)
                return
            htmlSource = htmlSource.text
            soup = BeautifulSoup(htmlSource, "lxml")
            print("This is the url that the program is attempting to download.", url)
            try:
                imageUrl = soup.select('link[rel=image_src]')[0].get('href')
            except IndexError:
                imageUrl = soup.find('meta', {'property' : 'og:image'})['content'] #The page has no image_src property  to get the link from so we go for the og:image property . 
            print("This is the image url that we've got so far: ",imageUrl)
            print("This is the image url that we've got so far: ",imageUrl)
            
            if imageUrl[0].startswith('//'):
                # if no schema is supplied in the url, prepend 'http:' to it
                imageUrl = 'http:' + imageUrl
    
            if '?' in imageUrl:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
            else:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:]
    
            localFileName = 'reddit_%s_%s_album_None_imgur_%s' % (targetSubreddit, submission.id, imageFile)
            if '/' in url:
                    localFileName.replace('/', '')
            downloadImgurImage(imageUrl, localFileName)
        else:
            print("This image or collection of images no longer exist!")
            return
    
def dhash(image, hash_size = 8):
    #Grayscale and shrink the image down.
    image=image.convert('L').resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS
    )
    
    
    #Compare the adjacent pixels
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col,row))
            pixel_right = image.getpixel((col+1, row))
            difference.append(pixel_left > pixel_right)
    image.close()       
    #Convert the binary array to a hexadecimal string.
    decimal_value = 0;
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
            
    return ''.join(hex_string)

def hamming_distance(s1, s2):
    # Return the Hamming distance between equal-length sequences
    if len(s1) != len(s2):
        raise ValueError("Undefined for sequences of unequal length")
    return float(sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2)))

def checkForDupes():
    imageHashes = {}
    thingsToDelete = []
    MINIMUM_HAMMING_DISTANCE  = .9 #An arbitrary number can change it later if it turns out i'm getting false positives. 
    IMGUR_REMOVED_PICTURE_HASH = "6f68969ad0218e0e" #I can't tell the difference between regular pictures and imgurs replaced pictures through source code scraping. This is hash from a removed image picture. Use it to check for others since they're all similar.
    totalPics = 1
    for i in os.listdir(os.getcwd()):
        if i.endswith(".jpg") or i.endswith(".jpeg") or i.endswith(".png") or i.endswith(".gif") or i.endswith(".apng"): #All the image types allowed by imgur. Anything not recognized just gets converted to png anyway.
            try:
                picture = Image.open(i)
            except Exception:
                print("For some reason the picture cannot be opened properly. This is usually because the OS does not recognize the image.")
                continue
            imageHash = dhash(picture)
            if hamming_distance(imageHash, IMGUR_REMOVED_PICTURE_HASH) < MINIMUM_HAMMING_DISTANCE: #Don't bother adding images that have been confirmed to be imgur auto removed images. Just append them to the thingsToDelete list.
                thingsToDelete.append(i)
            else:
                imageHashes[i] = imageHash
        picture.close()
        print("So far " + str(totalPics) + " have been proccessed, the current pic in progress is... " + i)
        totalPics+=1

        
            
            
    
    for original in imageHashes:
        if original in thingsToDelete:
            continue
        for comparason in imageHashes:
            if original == comparason:
                continue
            elif comparason in thingsToDelete:
                continue
            elif original == comparason:
                print ("The dupe function thinks that " + original + " and " + comparason + " are exact dupes of each other")
                thingsToDelete.apend(comparason)
            elif hamming_distance(imageHashes[original], imageHashes[comparason]) < MINIMUM_HAMMING_DISTANCE: #The closer to 0 the more similar the images are.
                print ("The dupe function thinks that " + original + " and " + comparason + " are near dupes of each other " + " " + str(hamming_distance(imageHashes[original], imageHashes[comparason])))
                print ("The original hash is " + imageHashes[original] + " and " + imageHashes[comparason])
                thingsToDelete.append(comparason)
    for image in thingsToDelete:
        print( "Deleting..." + image)
        os.remove(image)


def main():
 
    print("Welcome to the reddit mass imgur downloader.")
    if len(sys.argv) > 1 and sys.argv[1] == "-C":
        print("Welcome to the reddit mass imgur downloader dupe detection function!")
        print("This is an experimental feature. Please be prepared for hiccups")
        print("Beginning image dupe detection process!")
        checkForDupes()
    else:
        target_subreddit = input("Please input the name of the subreddit you want to download from: ")
        lower_date = input("Enter the date you want the program to start downloading from in the format d/m/y. If you want to start from the subreddit's creation press enter: ")
        upper_date = input("Enter the date you want the program to limit its downloading in the format d/m/y. If you want the upper bound to be today press enter: ")
        tags_to_ignore = input("Please input any words you want to use to filter out images. Seperate tags with a space. If you have no tags press enter: ")
        if lower_date != "":
            lower_date = int(humanToUnix(lower_date))
        if upper_date != "":
            upper_date = int(humanToUnix(upper_date))
        get_all_posts(target_subreddit, lower_date, upper_date, tags_to_ignore)
        print("Mass download complete!")
if __name__ == "__main__":
    main()



