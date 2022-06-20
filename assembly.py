from dataclasses import asdict
from uuid import uuid4
from shutil import make_archive

from bs4 import BeautifulSoup

from colors import Color, Colors, HeaderBackground, IconBackground
from content import DefragmentationOP, FileOP, TextOP, XMLOP, ArchiveCMD, TextCMD, XMLCMD, Content
from metadata import Metadata, Version, Author, Description, Licence


def camel_case(string: str):
    return ''.join((x.title() if i else x) for i, x in enumerate(string.split('_')))


class Assembly:
    def __init__(self, metadata: Metadata, colors: Colors, content: Content):
        self._uuid = uuid4()
        self.__metadata = metadata
        self.__colors = colors
        self.__content = content

    def build(self):
        with open('assembly.xml', 'rb') as tmp:
            template = tmp.read()
        soup = BeautifulSoup(template.decode(), 'xml')

        soup.package['version'] = '2.2'
        soup.package['id'] = f'{{{self._uuid}}}'

        metadata_tag = soup.find('metadata')
        metadata_tag.find('name').string = self.__metadata.name

        version_tag = metadata_tag.find('version')
        version_tag.find('major').string = str(self.__metadata.version.major)
        version_tag.find('minor').string = str(self.__metadata.version.minor)
        if self.__metadata.version.tag:
            tag = soup.new_tag('tag')
            tag.string = self.__metadata.version.tag
            version_tag.append(tag)

        author_tag = metadata_tag.find('author')
        author_tag.find('displayName').string = self.__metadata.author.display_name
        for attr, val in list(asdict(self.__metadata.author).items())[1:-1]:
            if not val:
                continue

            new_attr = soup.new_tag(camel_case(attr))
            new_attr.string = val
            author_tag.append(new_attr)

        if self.__metadata.author.youtube:
            author_tag.find('youtube')['linkKind'] = self.__metadata.author.youtube_link_kind

        description_tag = metadata_tag.find('description')
        description_tag.string = self.__metadata.description.text
        for attr, val in list(asdict(self.__metadata.description).items())[1:]:
            if val:
                description_tag[camel_case(attr)] = val

        if self.__metadata.large_description:
            large_description_tag = soup.new_tag('largeDescription')
            large_description_tag.string = self.__metadata.large_description.text
            for attr, val in list(asdict(self.__metadata.large_description).items())[1:]:
                if val:
                    large_description_tag[camel_case(attr)] = val
            metadata_tag.append(large_description_tag)

        if self.__metadata.licence:
            licence_tag = soup.new_tag('licence')
            licence_tag.string = self.__metadata.licence.text
            for attr, val in list(asdict(self.__metadata.licence).items())[1:]:
                if val:
                    licence_tag[camel_case(attr)] = val
            metadata_tag.append(licence_tag)

        colors_tag = soup.find('colors')
        header_background_tag = colors_tag.find('headerBackground')
        header_background_tag.string = '$' + self.__colors.header_background.color.HEX
        header_background_tag['useBlackTextColor'] = str(self.__colors.header_background.use_black_text_color)

        icon_background_tag = colors_tag.find('iconBackground')
        icon_background_tag.string = '$' + self.__colors.icon_background.color.HEX

        content_tag = soup.find('content')
        content_tag.append(self.__content.result)

        with open('package/assembly.xml', 'w') as f:
            f.write(soup.decode(formatter=None))

        make_archive('package', 'zip', 'package')
