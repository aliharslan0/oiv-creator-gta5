from dataclasses import dataclass, field


@dataclass(slots=True)
class Version:
    major: int
    minor: int
    tag: str = ''

    def __post_init__(self):
        if self.major < 0 and self.minor < 0:
            raise ValueError('"major" and "minor" must be greater than -1.')


@dataclass(slots=True)
class Author:
    display_name: str
    action_link: str = ''
    web: str = ''
    facebook: str = ''
    twitter: str = ''
    youtube: str = ''
    youtube_link_kind: str = ''

    def __post_init__(self):
        if self.youtube and self.youtube_link_kind == '':
            raise Exception(
                'If the "youtube" parameter is defined, the "youtube_link_kind" parameter must also be defined.')
        if self.youtube == '' and self.youtube_link_kind:
            raise Exception(
                'The "youtube_link_kind" parameter cannot be defined without defining the "youtube" parameter.')
        if self.youtube_link_kind and self.youtube_link_kind not in ['user', 'channel']:
            raise Exception('"youtube_link_kind" can only be defined as "user" or "channel".')


@dataclass(slots=True)
class Description:
    text: str
    footer_link: str = ''
    footer_link_title: str = ''

    def __post_init__(self):
        self.text = f'<![CDATA[{self.text}]]>'


@dataclass(slots=True)
class LargeDescription(Description):
    display_name: str = ''


@dataclass(slots=True)
class Licence(Description):
    pass


@dataclass(slots=True)
class Metadata:
    name: str
    version: Version
    author: Author
    description: Description
    large_description: LargeDescription = None
    licence: Licence = None
