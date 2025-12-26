import logging
from struct import pack
import asyncio
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


client1 = AsyncIOMotorClient(DATABASE_URI)
db1 = client1[DATABASE_NAME]
instance1 = Instance.from_db(db1)

client2 = AsyncIOMotorClient(DATABASE_URI2)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)


@instance1.register
class Media1(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME


@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME



async def save_file(media, use_db=1):
    model = Media1 if use_db == 1 else Media2
    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    exists_db1 = await Media1.find_one({"file_id": file_id})
    if exists_db1:
        logger.warning(f"File already exists in Media1 → Skipping save.")
        return False, 0

    exists_db2 = await Media2.find_one({"file_id": file_id})
    if exists_db2:
        logger.warning(f"File already exists in Media2 → Skipping save.")
        return False, 0
        
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = model(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:      
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
            )

            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1

import re
ADMIN_ID = 1733124290


ORDINALS = {
    "first": 1, "one": 1, "1st": 1,
    "second": 2, "two": 2, "2nd": 2,
    "third": 3, "three": 3, "3rd": 3,
    "fourth": 4, "four": 4, "4th": 4,
    "fifth": 5, "five": 5, "5th": 5,
    "sixth": 6, "six": 6, "6th": 6,
    "seventh": 7, "seven": 7, "7th": 7,
    "eighth": 8, "eight": 8, "8th": 8,
    "ninth": 9, "nine": 9, "9th": 9,
    "tenth": 10, "ten": 10, "10th": 10,
    # extend if needed
}

# Reverse map for expansion (1 → ["one", "first", "1st"])
REVERSE_ORDINALS = {}
for word, num in ORDINALS.items():
    REVERSE_ORDINALS.setdefault(num, set()).add(word)


def expand_numbers(query: str) -> list[str]:
    """Expand number/ordinal words into multiple variants."""
    tokens = query.lower().split()
    variants = [[]]

    for t in tokens:
        if t in ORDINALS:
            num = ORDINALS[t]
            equivalents = REVERSE_ORDINALS[num] | {str(num)}
            new_variants = []
            for v in variants:
                for eq in equivalents:
                    new_variants.append(v + [eq])
            variants = new_variants
        else:
            for v in variants:
                v.append(t)

    return [" ".join(v) for v in variants]


LANG_MAP = {
    "english": ["eng"], "eng": ["english"],
    "hindi": ["hin"], "hin": ["hindi"],
    "tamil": ["tam"], "tam": ["tamil"],
    "telugu": ["tel"], "tel": ["telugu"],
    "kannada": ["kan"], "kan": ["kannada"],
    "malayalam": ["mal"], "mal": ["malayalam"],
    "bengali": ["ben"], "ben": ["bengali"],
    "marathi": ["mar"], "mar": ["marathi"],
    "urdu": ["urd"], "urd": ["urdu"],
    "gujarati": ["guj"], "guj": ["gujarati"],
    "sanskrit": ["san"], "san": ["sanskrit"],
    "sinhala": ["sin"], "sin": ["sinhala"],
    "arabic": ["ara"], "ara": ["arabic"],
    "french": ["fre"], "fre": ["french"],
    "spanish": ["spa"], "spa": ["spanish"],
    "portuguese": ["por"], "por": ["portuguese"],
    "german": ["ger"], "ger": ["german"],
    "russian": ["rus"], "rus": ["russian"],
    "japanese": ["jap"], "jap": ["japanese"],
    "korean": ["kor"], "kor": ["korean"],
    "italian": ["ita"], "ita": ["italian"],
    "chinese": ["chi"], "chi": ["chinese"],
    "mandarin": ["man"], "man": ["mandarin"],
    "thai": ["tha"], "tha": ["thai"],
    "vietnamese": ["vie"], "vie": ["vietnamese"],
    "filipino": ["fil"], "fil": ["filipino"],
    "turkish": ["tur"], "tur": ["turkish"],
    "swedish": ["swe"], "swe": ["swedish"],
    "norwegian": ["nor"], "nor": ["norwegian"],
    "danish": ["dan"], "dan": ["danish"],
    "polish": ["pol"], "pol": ["polish"],
    "greek": ["gre"], "gre": ["greek"],
    "hebrew": ["heb"], "heb": ["hebrew"],
    "czech": ["cze"], "cze": ["czech"],
    "hungarian": ["hun"], "hun": ["hungarian"],
    "finnish": ["fin"], "fin": ["finnish"],
    "dutch": ["ned"], "ned": ["dutch"],
    "romanian": ["rom"], "rom": ["romanian"],
    "bulgarian": ["bul"], "bul": ["bulgarian"],
    "ukrainian": ["ukr"], "ukr": ["ukrainian"],
    "croatian": ["cro"], "cro": ["croatian"],
    "slovenian": ["slv"], "slv": ["slovenian"],
    "serbian": ["ser"], "ser": ["serbian"],
    "afrikaans": ["afr"], "afr": ["afrikaans"],
    "latin": ["lat"], "lat": ["latin"]
}


def expand_language_variants(query: str) -> list[str]:
    """Expand query for language keywords and their equivalents."""
    variants = [query]
    query_lower = query.lower()
    for lang, equivalents in LANG_MAP.items():
        if lang in query_lower:
            for eq in equivalents:
                if eq not in query_lower:
                    variants.append(query_lower.replace(lang, eq))
        elif any(eq in query_lower for eq in equivalents):
            for eq in equivalents:
                if eq in query_lower and lang not in query_lower:
                    variants.append(query_lower.replace(eq, lang))
    return variants


async def get_search_results(client, chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset, total_results)"""
    try:
        if chat_id is not None:
            settings = await get_settings(int(chat_id))
            try:
                if settings['max_btn']:
                    max_results = 10
                else:
                    max_results = int(MAX_B_TN)
            except KeyError:
                await save_group_settings(int(chat_id), 'max_btn', False)
                settings = await get_settings(int(chat_id))
                if settings['max_btn']:
                    max_results = 10
                else:
                    max_results = int(MAX_B_TN)

        query = query.strip()

        search_variants = expand_numbers(query)
        season_match = re.search(r"\b(?:season\s*(\d{1,2})|s0*(\d{1,2}))\b", query, re.IGNORECASE)
        # Episode detection
        episode_match = re.search(r"\b(?:episode\s*(\d{1,3})|e[p]?0*(\d{1,3}))\b", query, re.IGNORECASE)
        # Compact SxxEyy detection
        compact_match = re.search(r"\bS0*(\d{1,2})[\s._-]*E[P]?0*(\d{1,3})\b", query, re.IGNORECASE)

        if compact_match:
            sn, ep = int(compact_match.group(1)), int(compact_match.group(2))
            search_variants.append(re.sub(compact_match.re, f"S{sn:02d}E{ep:02d}", query))
            search_variants.append(re.sub(compact_match.re, f"S{sn}E{ep}", query))
            search_variants.append(re.sub(compact_match.re, f"Season {sn} Episode {ep}", query))

        if season_match and episode_match:
            sn = int(season_match.group(1) or season_match.group(2))
            ep = int(episode_match.group(1) or episode_match.group(2))
                
                # Replace season and episode in the original query using spans
            start, end = min(season_match.start(), episode_match.start()), max(season_match.end(), episode_match.end())
            replaced = query[:start] + f"S{sn:02d}E{ep:02d}" + query[end:]
            search_variants.append(replaced)
            replaced2 = query[:start] + f"S{sn}E{ep}" + query[end:]
            search_variants.append(replaced2)
            replaced3 = query[:start] + f"Season {sn} Episode {ep}" + query[end:]
            search_variants.append(replaced3)


        if season_match:
            sn = int(season_match.group(1) or season_match.group(2))
            search_variants.append(re.sub(season_match.re, f"S{sn:02d}", query))
            search_variants.append(re.sub(season_match.re, f"Season {sn}", query))

        if episode_match:
            ep = int(episode_match.group(1) or episode_match.group(2))
            search_variants.append(re.sub(episode_match.re, f"E{ep:02d}", query))
            search_variants.append(re.sub(episode_match.re, f"EP {ep:02d}", query))
            search_variants.append(re.sub(episode_match.re, f"EP{ep}", query))
            search_variants.append(re.sub(episode_match.re, f"Episode {ep}", query))
            for syd in range(1, 9):  # for seasons 1 to 10
                search_variants.append(re.sub(episode_match.re, f"S{syd:02d}E{ep:02d}", query))
                search_variants.append(re.sub(episode_match.re, f"S{syd}E{ep}", query))

        # Expand language keywords
        search_variants.append(re.sub("&", "and", query))

        # Expand language keywords
        expanded_variants = []
        for q in search_variants:
            expanded_variants.extend(expand_language_variants(q))
        search_variants = list(set(expanded_variants))  # remove duplicates

        regex_list = []
        for q in search_variants:
            if not q:
                raw_pattern = "."
            elif " " not in q:
                raw_pattern = rf"(\b|[\.\+\-_]){re.escape(q)}(\b|[\.\+\-_])"
            else:
                escaped_q = re.escape(q)
                raw_pattern = escaped_q.replace(r"\ ", r".*[\s\.\+\-_]")

            try:
                regex_list.append(re.compile(raw_pattern, flags=re.IGNORECASE))
            except Exception as e:
                await client.send_message(
                    ADMIN_ID,
                    f"⚠️ Regex compile failed\nQuery: `{q}`\nPattern: `{raw_pattern}`\nError: `{e}`"
                )
                continue

        

        #if USE_CAPTION_FILTER:
           # filter = {"$or": [{"file_name": {"$in": regex_list}}, {"caption": {"$in": regex_list}}]}
       # else:
           # filter = {"file_name": {"$in": regex_list}}

       # if file_type:
          #  filter["file_type"] = file_type

       # cursor = Media.find(filter, {"file_name": 1, "caption": 1, "file_size": 1, "file_id": 1})
        #cursor.sort("$natural", -1).skip(offset).limit(max_results + 1)
      #  docs = await cursor.to_list(length=max_results + 1)

       # files = docs[:max_results]
       # next_offset = offset + max_results if len(docs) > max_results else ""
       # total_results = offset + len(files)


       # return files, next_offset, total_results
                   # after building regex_list
            # after building regex_list
    

        filter = {"file_name": {"$in": regex_list}}
        if file_type:
            filter["file_type"] = file_type


        async def search_db(model):
            cursor = model.find(filter)
            cursor.sort("$natural", -1).skip(offset).limit(max_results)
            files = await cursor.to_list(length=max_results)
            count = await model.count_documents(filter)
            return files, count

        (files1, count1), (files2, count2) = await asyncio.gather(
            search_db(Media1),
            search_db(Media2)
        )

        combined = files1 + files2
        combined = combined[:max_results]

        total_results = count1 + count2

        next_offset = offset + max_results if (offset + max_results) < total_results else ""

        return combined, next_offset, total_results
        
    # get total matching results (can be slow for huge collection)
        total_results = await Media.count_documents(filter)

    # fetch only what we need
        cursor = Media.find(filter)
        cursor.sort("$natural", -1)
        cursor.skip(offset).limit(max_results)
        files = await cursor.to_list(length=max_results)

    # calculate next offset (allowing total_results to exceed max_results)
        next_offset = offset + max_results if (offset + max_results) < total_results else ""

        return files, next_offset, total_results


    except Exception as e:
        await client.send_message(
            ADMIN_ID,
            f"❌ Error in get_search_results\nChat: `{chat_id}`\nQuery: `{query}`\nError: `{e}`"
        )
        return [], "", 0

async def get_sch_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media1.count_documents(filter)

    cursor = Media1.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Get list of files
    files = await cursor.to_list(length=total_results)

    return files, total_results

async def get_file_details(query):
    filter = {"file_id": query}
    file1 = await Media1.find_one(filter)
    if file1:
        return [file1]
    file2 = await Media2.find_one(filter)
    if file2:
        return [file2]
    return []


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
