import os
import trio


class StringBuilder:
    """
    python class for efficient string concatenation and building
    """
    def __init__(self, max_length=None, sep=''):
        self.subs = []
        self.sep = sep

    def append(self, sub):
        """
        appends sub string to the existing string

        :param sub: sub-string to be appended
        :return:
            :boolean:
            True if the sub string appended correctly
            False if the string length after the appending will exceed the maximum length
        """
        self.subs.append(str(sub))
        self.subs.append(self.sep)

    def newline(self):
        self.subs[-1] = os.linesep

    def build(self):
        """
        builds the string
        :return:
         string of appended sub-strings
        """
        full_str = ''.join(self.subs)
        self.subs = []
        return full_str


class ScanRecorder:
    def __init__(self, basename):
        self.folder = './data'
        self.ext = 'txt'
        self.headers = []
        self.sb = StringBuilder(sep=', ')
        self.base_name = basename
        self.file = None

    def new_file(self):
        self.headers = []
        self._check_folder()
        unique_name = self._get_unique_name(self.base_name)
        self.file = open(unique_name, 'w')
        return

    async def receive_vals(self, mem_channel):
        async with mem_channel:
            self.new_file()
            async for line in mem_channel:
                print(f"got: {line}")
                if line is "NEWFILE":
                    self.new_file()
                    continue
                self._write_line(line)
        print("fclose")
        self.file.close()

    def _write_line(self, raw_line:dict):
        if not self.headers:
            self.set_headers(raw_line)
            self.write_headers()
        for field in self.headers:
            self.sb.append(raw_line[field])
        self.sb.newline()
        self.file.write(self.sb.build())

    def set_headers(self, fields: dict):
        for k in fields.keys():
            self.headers.append(k)

    def write_headers(self):
        for field in self.headers:
            self.sb.append(field)
        self.sb.newline()

    def close(self):
        if self.file:
            self.file.close()

    def _check_folder(self):
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def _get_unique_name(self, filename_base: str) -> str:
        id = f"{self.folder}{os.sep}{filename_base}.{self.ext}"
        if not os.path.exists(id):
            return id
        i = 0
        while True:
            id = f"{self.folder}{os.sep}{filename_base}_{i}.{self.ext}"
            if not os.path.exists(id):
                return id
            i += 1
