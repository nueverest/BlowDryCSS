from cssutils import parseString
from string import ascii_lowercase, digits
__author__ = 'chad nelson'
__project__ = 'blow dry css'


class ClassPropertyParser(object):
    # Class Format Legend
    # Dashes separate word in multi-word property names/aliases.
    # property-name
    # font-weight
    #
    # Dashes separate CSS property_name/alias from property_value
    # alias-value
    # font-weight-700
    #
    # Dashes separate multiple values for properties that take multiple values.
    # alias-value-value-value-value
    # padding-10-20-10-10
    #
    # Dashes separate !important priority indicator '-i' (append to the end of the string)
    # alias-value-i
    # font-weight-bold-i
    #
    # Shorthand can be used in cases where the alias is the unambiguously the value.
    # alias = value
    # font-weight-bold OR bold OR b
    # font-weight-bold-i OR bold-i OR b-i
    def __init__(self, class_set=set()):
        css = u'''/* Generated with BlowDryCSS. */'''
        self.sheet = parseString(css)
        self.rules = []
        self.importance_designator = '-i'       # '-i' is used to designate that the priority level is '!important'
        self.removed_class_set = set()
        self.class_set = class_set
        self.clean_class_set()

        # TODO: move this to a CSV file and autogenerate this dictionary from CSV.
        # Dictionary contains:
        #   css property name as 'keys'
        #   list of aliases as 'values' - An alias can be shorthand for the property name.
        self.property_dict = {
            'font-weight': ['normal', 'bold', 'bolder', 'lighter', 'initial', 'fw-'],
        }

    # Take list, tuple, or set of strings an convert to lowercase.
    def class_set_to_lowercase(self):
        self.class_set = {css_class.lower() for css_class in self.class_set}

    # Validate underscore usage in a single css_class.
    # Underscores are only allowed to designate a decimal point between numbers.
    #   Valid: '6_3'
    # Invalid: '_b', 'b_', 'padding-_2", '2_rem', 'm_px', and '__'
    @staticmethod
    def underscores_valid(css_class=''):
        # underscore is not allowed to be the first or last character of css_class
        if css_class[0] == '_' or css_class[-1] == '_':
            return False

        # Check character before and after underscore index.
        index = css_class.find('_')
        allowed_before = set(digits)
        allowed_after = set(digits)
        if index > 0:                                                   # Underscore is not the first character.
            valid = set(css_class[index-1]) <= allowed_before           # Check Character before
            valid = valid and set(css_class[index+1]) <= allowed_after  # Check Character after.
        else:
            valid = True

        return valid

    # Detect and Remove invalid css classes from class_set
    # Class names must abide by: http://www.w3.org/TR/CSS2/syndata.html#characters
    # For purposes of this library only a SUBSET of the standard is permissible as follows:
    # Classes are only allowed to begin with [a-z]
    # Classes are only allowed to end with [a-z0-9]
    # Classes are allowed to contain [_a-z0-9-]
    # Underscores are only allowed between digits [0-9]
    # Reference: stackoverflow.com/questions/1323364/in-python-how-to-check-if-a-string-only-contains-certain-characters
    def clean_class_set(self):
        # Set all strings to lowercase first.
        self.class_set_to_lowercase()

        # Validate against character sets.
        allowed_first = set(ascii_lowercase)
        allowed_middle = set(ascii_lowercase + digits + '_-')
        allowed_last = set(ascii_lowercase + digits)

        # Gather invalid_css_classes
        invalid_css_classes = set()
        for css_class in self.class_set:
            if not set(css_class[0]) <= allowed_first:              # First character
                invalid_css_classes.add(css_class)
            if not set(css_class) <= allowed_middle:                # All characters
                invalid_css_classes.add(css_class)
            if not set(css_class[-1]) <= allowed_last:              # Last character
                invalid_css_classes.add(css_class)
            if not self.underscores_valid(css_class=css_class):     # Underscore
                invalid_css_classes.add(css_class)

        # Remove invalid_css_classes from self.class_set
        for invalid_css_class in invalid_css_classes:
            self.class_set.remove(invalid_css_class)
            self.removed_class_set.add(invalid_css_class)

    # Property Name
    #
    # Class returns the property_name or removes/cleans the unrecognized class and returns ''.
    # Classes that use identical property names must set a property value
    # i.e. 'font-weight' is invalid because no value is included AND 'font-weight-700' is valid because 700 is a value.
    def get_property_name(self, css_class=''):
        for property_name, aliases in self.property_dict.items():
            # Try identical match first. An exact match must also end with a '-' dash to be valid.
            if css_class.startswith(property_name + '-'):
                return property_name

            # Try matching with alias. An alias is not required to end with a dash.
            for alias in aliases:
                if css_class.startswith(alias):
                    return property_name

            # No match found. Remove from class_set.
            self.class_set.remove(css_class)
            self.removed_class_set.add(css_class)
            return ''

    # Strip property name from encoded_property_value if applicable and return encoded_property_value.
    @staticmethod
    def strip_property_name(property_name='', encoded_property_value=''):
        # Deny empty string. If it doesn't have a property name ignore it.
        if property_name == '':
            raise ValueError('CSS property_name cannot be empty.')
        # Append '-' to property to match the class format.
        else:
            property_name += '-'

        # Strip property name
        if encoded_property_value.startswith(property_name):
            return encoded_property_value[len(property_name):]
        else:
            return encoded_property_value

    # Some alias could be abbreviations e.g. 'fw-' stands for 'font-weight-'
    # In these cases a dash is added in the dictionary to indicate an abbreviation.
    @staticmethod
    def alias_is_abbreviation(alias=''):
        return alias.endswith('-')

    # Returns a list of all property abbreviations appearing in property_dict
    def get_property_abbreviations(self, property_name=''):
        property_abbreviations = list()
        for property_name, aliases in self.property_dict.items():
            for alias in aliases:
                if self.alias_is_abbreviation(alias=alias):
                    property_abbreviations.append(alias)

        return property_abbreviations

    # Strip property abbreviation from encoded_property_value if applicable and return encoded_property_value.
    def strip_property_abbreviation(self, property_name='', encoded_property_value=''):
        property_abbreviations = self.get_property_abbreviations(property_name=property_name)

        for property_abbreviation in property_abbreviations:
            if encoded_property_value.startswith(property_abbreviation):
                return encoded_property_value[len(property_name):]

        return encoded_property_value

    # Property Value
    #
    # Strip property name or abbreviation prefix and property priority designator
    # Examples:
    # 'fw-bold-i' --> 'bold'                [abbreviated font-weight property_name]
    # 'padding-1-10-10-5-i' --> '1-10-10-5' [standard property_name]
    # 'height-7_25rem-i' --> '7_25rem'      [contains underscores]
    # The term encoded_property_value means a property value that may or may not contain dashes and underscores.
    def get_encoded_property_value(self, property_name='', css_class=''):
        encoded_property_value = css_class
        encoded_property_value = self.strip_property_name(encoded_property_value=encoded_property_value)
        encoded_property_value = self.strip_property_abbreviation(encoded_property_value=encoded_property_value)
        encoded_property_value = self.strip_priority_designator(encoded_property_value=encoded_property_value)
        return encoded_property_value

    # Accepts an encoded_property_value that's been stripped of it's property named and priority
    # Returns the property value.
    def get_property_value(self, encoded_property_value=''):
        # TODO: Call CSSPropertyValueParser
        return ''

    # Property Priority
    #
    def is_important(self, css_class=''):
        return css_class.endswith(self.importance_designator)

    # Strip priority designator from the end of enconded_property_value.
    def strip_priority_designator(self, encoded_property_value=''):
        if self.is_important(css_class=encoded_property_value):
            return encoded_property_value[:-len(self.importance_designator)]
        else:
            return encoded_property_value

    def get_property_priority(self, css_class=''):
        return 'IMPORTANT' if self.is_important(css_class=css_class) else ''


# Accepts a clean encoded_property_value.
# Generates a valid css property_value
class CSSPropertyValueParser(object):
    def __init__(self, encoded_property_value=''):
        if not '-' in encoded_property_value:
            self.property_value = encoded_property_value
        else:
            # TODO: Handle values and units 12px or 1o32rem or 25p
            pass

    # '-' becomes spaces    example: 1-5-1-5 --> 1 5 1 5
    def replace_dashes(self):
        self.property_value.replace('-', ' ')

    # '_' becomes '.'   example: 1_32rem --> 1.32rem
    def replace_underscore(self):
        self.property_value.replace('_', '.')

    # TODO: handle percentage case i.e. padding-1p-10p-3p-1p --> 1% 10% 3% 1%

    # convert px to rem
    def px_to_em(self, px):
        # TODO: write this.
        pass