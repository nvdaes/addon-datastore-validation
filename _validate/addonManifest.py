#!/usr/bin/env python

from configobj import ConfigObj
from io import StringIO


class AddonManifest(ConfigObj):
	""" Add-on manifest file. It contains metadata about an NVDA add-on package. """
	configspec = ConfigObj(StringIO(
		"""
# NVDA Add-on Manifest configuration specification
# Add-on unique name
name = string()

# short  summary (label) of the add-on to show to users.
summary = string()

# Long description with further information and instructions
description = string(default=None)

# Name of the author or entity that created the add-on
author = string()

# Version of the add-on. Should preferably in some standard format such as x.y.z
version = string()

# The minimum required NVDA version for this add-on to work correctly.
# Should be less than or equal to lastTestedNVDAVersion
minimumNVDAVersion = apiVersion(default="0.0.0")

# Must be greater than or equal to minimumNVDAVersion
lastTestedNVDAVersion = apiVersion(default="0.0.0")

# URL for more information about the add-on. New versions and such.
url= string(default=None)

# Name of default documentation file for the add-on.
docFileName = string(default=None)

# NOTE: apiVersion:
# EG: 2019.1.0 or 0.0.0
# Must have 3 integers separated by dots.
# The first integer must be a Year (4 characters)
# "0.0.0" is also valid.
# The final integer can be left out, and in that case will default to 0. E.g. 2019.1

"""))

	def __init__(self, input, translatedInput=None):
		""" Constructs an L{AddonManifest} instance from manifest string data
		@param input: data to read the manifest information
		@type input: a fie-like object.
		@param translatedInput: translated manifest input
		@type translatedInput: file-like object
		"""
		super().__init__(
			input,
			configspec=self.configspec,
			encoding='utf-8',
			default_encoding='utf-8'
		)
		self._errors = None
		if not self._validateApiVersionRange():
			self._errors = "Constraint not met: minimumNVDAVersion ({}) <= lastTestedNVDAVersion ({})".format(
				self.get("minimumNVDAVersion"),
				self.get("lastTestedNVDAVersion")
			)
		self._translatedConfig = None
		if translatedInput is not None:
			self._translatedConfig = ConfigObj(translatedInput, encoding='utf-8', default_encoding='utf-8')
			for k in ('summary', 'description'):
				val = self._translatedConfig.get(k)
				if val:
					self[k] = val

	@property
	def errors(self):
		return self._errors

	def _validateApiVersionRange(self):
		lastTested = self.get("lastTestedNVDAVersion")
		minRequiredVersion = self.get("minimumNVDAVersion")
		return minRequiredVersion <= lastTested
