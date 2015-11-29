from cssutils.css import Property
from xml.dom import SyntaxErr
# custom
from utilities import contains_a_digit
from colorparser import ColorParser
from unitparser import UnitParser
#from mediaparser import MediaParser
__author__ = 'chad nelson'
__project__ = 'blow dry css'


# Accepts a clean encoded_property_value e.g. 'bold', '1-5-1-5', '1_32rem', '1p-10p-3p-1p', 'n12px', 'n5_25cm-n6_1cm'
# Decodes a css property_value from a clean encoded_property_value.
class CSSPropertyValueParser(object):
    def __init__(self, px_to_em=True):
        self.color_parser = ColorParser()
        self.unit_parser = UnitParser(px_to_em=px_to_em)
    
    # Important: these methods are intended to be called in the order they are declared.

    # Delete leading    example: '-bold' --> 'bold'
    # Delete trailing   example: 'white-' --> 'white'
    # Replace internal  example: '1-5-1-5' --> '1 5 1 5'
    @staticmethod
    def replace_dashes(value=''):
        value = value[1:] if value.startswith('-') else value
        value = value[:-1] if value.endswith('-') else value
        return value.replace('-', ' ')

    # Use underscores to indicate Decimal point '_' --> '.'
    # '_' becomes '.'   example: '1_32rem' --> '1.32rem'
    def replace_underscore_with_decimal(self, value=''):
        if contains_a_digit(value=value):
            value = value.replace('_', '.')
        return value

    # Using Percentages 'p' --> '%'
    # mind the space
    # 'p ' becomes '% ' example: '1p 10p 3p 1p' --> '1% 10% 3% 1%' AND ' 1p' --> ' 1%'
    def replace_p_with_percent(self, value=''):
        if contains_a_digit(value=value):
            value = value.replace('p ', '% ')
            if value.endswith('p'):
                value = value[:-1] + '%'    # chop last character and add percentage sign
        return value

    # Declaring negative values
    # mind the space
    # ' n' becomes ' -'
    # examples:
    # 'n5cm n6cm' --> '-5cm -6cm'
    # 'n9in' --> '-9in' (note that the 'n' at the end is not touched)
    def replace_n_with_minus(self, value=''):
        if contains_a_digit(value=value):
            value = value.replace(' n', ' -')
            if value.startswith('n'):
                value = '-' + value[1:]     # add minus sign and chop first character
        return value

    # Put everything together.
    def decode_property_value(self, property_name='', value=''):
        # Apply to all.
        value = self.replace_dashes(value=value)

        # These only apply if value contains a digit.
        value = self.replace_underscore_with_decimal(value=value)
        value = self.replace_p_with_percent(value=value)
        value = self.replace_n_with_minus(value=value)

        # Add plugins here
        value = self.color_parser.replace_h_with_hash(property_name=property_name, value=value)
        value = self.color_parser.add_color_parenthetical(property_name=property_name, value=value)
        value = self.unit_parser.add_units(property_name=property_name, property_value=value)           # Add units if necessary.
        return value

    # Accepts a property name and value
    # Validation occurs after the property value is decoded.
    @staticmethod
    def property_is_valid(name='', value='', priority=''):
        try:
            css_property = Property(name=name, value=value, priority=priority)
            is_valid = css_property.valid
            return is_valid
        except SyntaxErr:
            return False

# TODO: Are URIs ridiculous? or should we implement syntax.  For now YES they are ridiculous
# background-image-url-image.png --> background-image: url("image.png")
# background-image-url-_home_images_sample_image.png --> background-image: url("/home/images/sample/image.png")
# IN THE LAST CASE images with underscores would not work could use a double underscore to represent final directory
# but this is getting ridiculous example double underscore signifies final directory
# allowing underscore in file name:
# background-image-url-_home_images_sample__image_1.png --> background-image: url("/home/images/sample/image_1.png")
