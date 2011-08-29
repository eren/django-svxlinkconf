#!/usr/bin/python
# -*- coding: utf-8 -*-


from collections import OrderedDict
import iniparse


"""
This module provides a way of manipulating svxlink.conf.

.. moduleauthor:: Eren Türkay <eren@pardus.org.tr>

"""
__author__    = "Eren Türkay"
__email__     = "eren@pardus.org.tr"
__copyright__ = "Copyright 2011"
__license__   = "GPLv2"
__version__   = "0.1"

class SvxlinkTypeContainer(object):

    def __init__(self, type_name, section_name, valid_options, data=None):
        """Type container for Svxlink Types.

        It serves as an abstract class. We need to check for valid options
        when setting sections. Instead of copying/pasting the code, this
        abstract class checks for valid options when setting an item in class.

        __dbase__ is an internal representation of key/values with an
        OrderedDict. If data is provided, __dbase__ is filled with this
        data.  Otherwise, we know that the section is created from
        scratch so we add TYPE accordingly to type_name argument by
        default.  "Data" is an array of tuple because it's the type that
        ConfigParser returns. For the ease of use, it's directly used in
        this way.

        Note that svxlink.conf requires UPPERCASE for options in sections.
        Section names can be arbitrary, however, options are presented
        upper-case. Whenever you set an option name, it will be converted to
        uppercase. It does not matter the way you set options. For
        example:

        f = SvxlinkTypeNet("foo")
        f["tcp_PORT" = 5220

        is converted to:

        f["TCP_PORT"] 5220

        so it's still valid to use as long as option is present in
        VALID_OPTIONS

        """

        # TODO: Implement a checker function. Now, we only check for
        # valid options, not the values themselves. Later, we would need
        # to check for values so we need to implement a function that
        # checks it. Additionally, this function will be unique to the
        # classes that extends SvxlinkTypeContainer. So it should be
        # optional in __init__()

        self._VALID_OPTIONS = valid_options
        self._TYPE_NAME = type_name
        self._SECTION_NAME = section_name

        # internal ordered dictionary for storing key/values typical to
        # section
        self.__dbase__ = OrderedDict()

        if data is None:
            self.__dbase__.update({"TYPE": type_name})
        else:
            # start adding values that are in tuple to __dict__
            for tuple_item in data:
                self.__check_item_and_update(tuple_item[0],
                                             tuple_item[1])

    def __check_item_and_update(self, key, val):
        """Checks the item in VALID_OPTIONS and updates __dbase__ if the
        option is valid.

        """
        if not key.upper() in self._VALID_OPTIONS:
            raise ValueError("Option '%s' is not valid for '%s'" %
                    key, self._SECTION_NAME)

        self.__dbase__.update({key.upper(): val})


    def __str__(self):
        return "<Svxlink-%s: %s>" % (self._TYPE_NAME, self._SECTION_NAME)

    def __getitem__(self, key):
        return self.__dbase__.get(key.upper());

    def __setitem__(self, key, val):
        self.__check_item_and_update(key, val)

    def get_section_name(self):
        """Returns a section name"""

        return self._SECTION_NAME

    def has_option(self, option):
        """Checks if there is an option in __dict__

        """

        return self.__dbase__.has_key(option.upper())

    def items(self):
        """Returns ConfigParser compatable output for items in this section.

        The output is an array of tuples such as:

        [(tcp_port, 5220), (type, "Net")]

        """

        # iterate over __dict__, do not take variables that start with _
        # into account.
        output = []
        for item in self.__dbase__:
            if not item.startswith("_"):
                output.append((item, self[item]))

        return output

class SvxlinkTypeNet(SvxlinkTypeContainer):
    """The class that represents TYPE=Net section in svxlink

    """

    def __init__(self, section_name, data=None):
        """Initializes the class. It serves as a container for TYPE=Net.

        :param section_name: Name of the section.
        :param data: **(Optional)** An array of (name, value) pair.  For
        example [('host', 'localhost'), ('tcp_port', '5220')]

        """

        # TODO: Add SPEEX_ENC_*, SPEEX_DEC_* options here
        super(SvxlinkTypeNet, self).__init__("Net", section_name,
                ["TYPE", "HOST", "TCP_PORT", "AUTH_KEY", "CODEC"],
                data)

    def is_online(self):
        """Checks if the host is up and running.

        """

        if not (self.has_option("TCP_PORT") and
                self.has_option("HOST")):
            raise ValueError("TCP_PORT and HOST should be set for this function to run")

        # FIXME: Maybe we should import it at top?
        import socket

        # we need 3 second delay at most, otherwise we may think that
        # host is not running.
        socket.setdefaulttimeout(3.00)
        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)

        try:
            s.connect((self["HOST"], self["TCP_PORT"]))
            return True
        except:
            # FIXME: For debug purposes, we need to get what the
            # exception was
            return False


class SvxlinkTypeMulti(SvxlinkTypeContainer):
    def __init__(self, section_name, data=None):
        """Initializes the class. It serves as a container for TYPE=Multi.

        :param section_name: Name of the section.
        :param data: **(Optional)** An array of (name, value) pair.  For
        example [('transmitters', 'Istanbul,Ankara')]

        """

        super(SvxlinkMulti, self).__init__("Multi", section_name,
                ["TRANSMITTERS"],
                data)


class SvxlinkConf():
    """Main class


    """

    def __init__(self, config_file="/etc/svxlink/svxlink.conf"):
        """Initialize the class.

        Initializes the class. Be sure that the file exists before
        using this class as we do not control whether the file exists or
        not

        :param config_file: Config file to read or manipulate ** (default:
            /etc/svxlink/svxlink.conf)**
        :type config_file: string

        """

        parser = iniparse.ConfigParser()
        parser.read(config_file)

        self.config = parser


    def get_remote_nodes(self):
        """Lists nodes that are TYPE=Net

        Iterate over TYPE=Net section and list the remote nodes as
        SvxlinkTypeNet object.

        :returns: An array of SvxlinkTypeNet object.
        :rtype: array

        """

        sections = self.config.sections()

        # Get sections which have "TYPE" option. GLOBAL for example does
        # not have this option so we would get NoOptionError exception.
        # Additionally, filter only Net type
        remote_nodes = filter(lambda x: (self.config.has_option(x, "TYPE") and
                self.config.get(x, "TYPE") == "Net"), sections)

        return map(lambda x: SvxlinkTypeNet(x, self.config.items(x)), remote_nodes)

    def add_section(self, sectionObj):
        """Adds a section to main svxlink.conf.

        :param sectionObj: An object to add
        :type sectionObj: One of the SvxlinkType* objects.

        """

        section_name = sectionObj.get_section_name()
        self.config.add_section(section_name)

        for item in sectionObj.items():
            print item
            self.config.set(section_name, item[0], item[1])

    def write(self, file_name, mode="a"):
        """Save changes in the configuration file

        :param file_name: File name to write to
        :type file_name: String
        :param mode: Mode that is used to open the file. **(Default: a)**
        :type mode: String

        """

        fp = open(file_name, mode)
        self.config.write(fp)
        fp.close()


    def foo(self):
        #f = SvxlinkTypeNet("ErenTurkay", [("tcp_port", "5220"), ("auth_key", "testtest")])
        f = SvxlinkTypeNet("ErenTurkay")
        f["tcp_port"] = 5220
        f["host"] = "localhost"

        self.add_section(f)

        f.items()

if __name__ == '__main__':
    f = SvxlinkConf("etc/svxlink.conf")

#    for remote in f.get_remote_nodes():
#        print "%s" % remote

    f.foo()

