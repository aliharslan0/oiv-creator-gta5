from dataclasses import dataclass, field
from bs4 import BeautifulSoup


@dataclass(slots=True)
class Command:
    command: str = field(init=False)


@dataclass(slots=True)
class DefragmentationOP(Command):
    archive: str

    def __post_init__(self):
        self.command = f'<defragmentation archive="{self.archive}"/>'


@dataclass(slots=True)
class FileOP(Command):
    mode: str
    file: str
    source: str = ''

    def __post_init__(self):
        if self.mode not in ('add', 'delete'):
            raise Exception('Mode must be "add" or "delete".')
        if self.mode == 'add' and not self.source:
            raise Exception('If mode is defined as "add", the source parameter must also be defined.')
        elif self.mode == 'delete' and self.source:
            raise Exception('When the mode is defined as "delete", the source parameter must not be defined.')

        template = '<{mode}{source}>{file}</{mode}>'
        self.command = template.format(mode=self.mode, file=self.file,
                                       source=f' source="{self.source}"' if self.mode == 'add' else '')


@dataclass(slots=True)
class TextOP(Command):
    mode: str
    text: str
    where: str = ''
    line: str = ''
    condition: str = ''

    def __post_init__(self):
        match self.mode:
            case 'add':
                if self.where or self.line or self.condition:
                    raise Exception('You cannot use other parameters in "add" mode.')
            case 'insert':
                if not all(x for x in (self.where, self.line, self.condition)):
                    raise Exception('In "insert" mode all parameters must be filled in.')
            case 'replace':
                if not all(x for x in (self.line, self.condition)):
                    raise Exception('In "replace" mode, line and condition parameters must be filled.')
            case 'delete':
                if not self.condition:
                    raise Exception('In "delete" mode, the condition parameter must be filled in.')
            case _:
                raise Exception('Mode must be one of "add", "insert", "replace" or "delete".')

        if self.where and self.where not in ('Before', 'After'):
            raise Exception('Where can only be defined as "After" or "Before".')
        if self.condition and self.condition not in ('Equal', 'StartsWith', 'Mask'):
            raise Exception('Condition can only be defined as "Equal", "StartsWith" and "Mask".')

        template = '<{mode}{where}{line}{condition}>{text}</{mode}>'
        self.command = template.format(mode=self.mode, text=self.text,
                                       where=f' where="{self.where}"' if self.mode == 'insert' else '',
                                       line=f' line="{self.line}"' if self.mode in ('insert', 'replace') else '',
                                       condition=f' condition="{self.condition}"' if self.mode in (
                                       'insert', 'replace', 'delete') else '')


@dataclass(slots=True)
class XMLOP(Command):
    mode: str
    xpath: str
    append: str = ''
    node_value: str = ''
    node_tag: str = 'Item'
    node_attrs: list[tuple[str, str]] = field(default_factory=lambda: [])

    def __post_init__(self):
        if self.mode not in ('add', 'replace', 'remove'):
            raise Exception('Mode can only be "add", "replace" or "remove".')

        if self.mode == 'add' and not all(x for x in (self.append, self.node_value)):
            raise Exception('All parameters must be entered when mode is "add".')
        elif self.mode != 'add' and self.append:
            raise Exception('The append parameter can only be used in "add" mode.')
        elif self.append and self.append not in ('First', 'Last', 'Before', 'After'):
            raise Exception('Append can only be defined as "First", "Last", "Before" and "After".')

        if self.mode == 'replace' and not self.node_value:
            raise Exception('When mode is replace, the node_value parameter must be entered.')

        if self.mode == 'remove' and (self.append or self.node_tag != 'Item' or self.node_attrs or self.node_value):
            raise Exception('Only the xpath parameter can be used in remove mode.')

        if self.mode != 'remove':
            parent_template = '<{mode}{append}{xpath}></{mode}>'
            parent = parent_template.format(mode=self.mode, xpath=f' xpath="{self.xpath}"',
                                            append=f' append="{self.append}"' if self.mode == 'add' else '')
            child_template = '<{tag}{attrs}>{value}</{tag}>'
            child = child_template.format(tag=self.node_tag, value=self.node_value,
                                          attrs=' '.join([f'{k}="{v}"' for k, v in self.node_attrs]))
            soup = BeautifulSoup(parent, 'xml')
            soup.find(self.mode).append(child)
            self.command = soup.decode_contents(formatter=None)
        else:
            self.command = f'<remove xpath="{self.xpath}"/>'


@dataclass(slots=True)
class NestedCMD(Command):
    path: str
    commands: list[Command]

    def __post_init__(self):
        archive_template = '<archive path="{0}" createIfNotExist="{1}" type="{2}"></archive>'
        text_template = '<text path="{0}" createIfNotExist="{1}"></text>'
        xml_template = '<xml path="{0}"></xml>'

        def init_nested(nested_cmd: NestedCMD):
            if isinstance(nested_cmd, ArchiveCMD):
                nested_cmd.command = archive_template.format(nested_cmd.path, nested_cmd.create_if_not_exists,
                                                             nested_cmd.archive_type)
            elif isinstance(nested_cmd, TextCMD):
                nested_cmd.command = text_template.format(nested_cmd.path, nested_cmd.create_if_not_exists)
            elif isinstance(nested_cmd, XMLCMD):
                nested_cmd.command = xml_template.format(nested_cmd.path)

            soup = BeautifulSoup(nested_cmd.command, 'xml')
            nested_tag = soup.find(type(nested_cmd).__name__.lower()[:-3])

            for cmd in nested_cmd.commands:
                if isinstance(cmd, (FileOP, TextOP, XMLOP)):
                    nested_tag.append(cmd.command)
                elif isinstance(cmd, NestedCMD):
                    nested_tag.append(init_nested(cmd))

            return soup.decode_contents(formatter=None)

        self.command = init_nested(self)


@dataclass(slots=True)
class ArchiveCMD(NestedCMD):
    create_if_not_exists: bool
    archive_type: str = field(init=False, default='RPF7')


@dataclass(slots=True)
class TextCMD(NestedCMD):
    create_if_not_exists: bool
    commands: list[TextOP]


@dataclass(slots=True)
class XMLCMD(NestedCMD):
    commands = list[XMLOP]


@dataclass(slots=True)
class Content:
    commands: list[Command]
    result: str = field(init=False, repr=False)

    def __post_init__(self):
        soup = BeautifulSoup('<content></content>', 'xml')
        content_tag = soup.find('content')
        for cmd in self.commands:
            content_tag.append(cmd.command)
        self.result = soup.decode_contents(formatter=None)
