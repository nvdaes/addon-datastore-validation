#!/usr/bin/env python

# Copyright (C) 2021 Noelia Ruiz Martínez, NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html
from dataclasses import dataclass
import unittest
from unittest.mock import patch
import os
import json
from jsonschema import exceptions
from _validate import validate, addonManifest


VALID_ADDON_ID = "fake"

JSON_SCHEMA = validate.JSON_SCHEMA
TOP_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCE_DIR = os.path.dirname(TOP_DIR)
TEST_DATA_PATH = os.path.join(SOURCE_DIR, '_tests', 'testData')
ADDON_PACKAGE = os.path.join(TEST_DATA_PATH, f'{VALID_ADDON_ID}.nvda-addon')
ADDON_SUBMISSIONS_DIR = os.path.join(TEST_DATA_PATH, 'addons')
VALID_SUBMISSION_JSON_FILE = os.path.join(ADDON_SUBMISSIONS_DIR, VALID_ADDON_ID, '13.0.0.json')
MANIFEST_FILE = os.path.join(TEST_DATA_PATH, 'manifest.ini')


def getValidAddonSubmission() -> validate.JsonObjT:
	with open(VALID_SUBMISSION_JSON_FILE) as f:
		submission = json.load(f)
	return submission


def getAddonManifest():
	with open(MANIFEST_FILE) as f:
		manifest = addonManifest.AddonManifest(f)
	return manifest


class Validate_general(unittest.TestCase):
	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	def test_validateJson_SchemaNonConformance_Raises(self):
		self.submissionData["description"] = 3  # should be a string
		with self.assertRaises(exceptions.ValidationError):
			validate._validateJson(self.submissionData)


class Validate_checkDownloadUrlFormat(unittest.TestCase):
	"""Tests for the checkDownloadUrlFormat function
	"""
	def test_validExampleURL(self):
		url = (
			"https://github.com/nvdaes/clipContentsDesigner/releases/download/13.0/"
			"clipContentsDesigner-13.0.nvda-addon"
		)
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(errors, [])

	def test_minimalRequirementsURL(self):
		url = "https://something.nvda-addon"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(errors, [])

	def test_missingHTTPS(self):
		url = "http://something.nvda-addon"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			["Add-on download url must start with https://"]
		)

	def test_missingExt(self):
		url = "https://example.com"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			["Add-on download url must end with .nvda-addon"]
		)

	def test_missingHTTPsAndExt(self):
		url = "http://example.com"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			[
				"Add-on download url must start with https://",
				"Add-on download url must end with .nvda-addon",
			]
		)


class Validate_checkSha256(unittest.TestCase):
	"""Tests for the checkSha256 function
	"""
	validSha = "12ABBF6BAC89FC24602245F4B8B750BCF2B72AFDF2DF54A0B07467FF4983F872"

	def test_valid(self):
		errors = validate.checkSha256(
			ADDON_PACKAGE,
			expectedSha=self.validSha.upper()
		)
		self.assertEqual(list(errors), [])

		errors = validate.checkSha256(
			ADDON_PACKAGE,
			expectedSha=self.validSha.lower()
		)
		self.assertEqual(list(errors), [])

	def test_invalid(self):
		errors = validate.checkSha256(
			# just do a SHA for the manifest file so we don't need to include the whole *.nvda-addon file
			ADDON_PACKAGE,
			expectedSha='abc'
		)
		errors = list(errors)
		self.assertEqual(
			errors,
			[f"Sha256 of .nvda-addon at URL is: {self.validSha.lower()}"]
		)


class Validate_checkSummaryMatchesDisplayName(unittest.TestCase):
	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	def test_valid(self):
		errors = list(
			validate.checkSummaryMatchesDisplayName(self.manifest, self.submissionData)
		)
		self.assertEqual(errors, [])

	def test_invalid(self):
		badDisplayName = "bad display Name"
		self.submissionData["displayName"] = badDisplayName
		errors = list(
			validate.checkSummaryMatchesDisplayName(self.manifest, self.submissionData)
		)
		self.assertEqual(
			errors,
			[
				f"Submission 'displayName' must be set to '{self.manifest['summary']}' in json file."
				f" Instead got: '{badDisplayName}'"
			]
		)


class Validate_checkDescriptionMatches(unittest.TestCase):
	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	def test_valid(self):
		errors = list(
			validate.checkDescriptionMatches(self.manifest, self.submissionData)
		)
		self.assertEqual(errors, [])

	def test_invalid(self):
		badDesc = "bad description"
		self.submissionData["description"] = badDesc
		errors = list(
			validate.checkDescriptionMatches(self.manifest, self.submissionData)
		)
		self.assertEqual(
			errors,
			[
				f"Submission 'description' must be set to '{self.manifest['description']}' in json file."
				f" Instead got: '{badDesc}'"
			]
		)


class Validate_checkAddonId(unittest.TestCase):
	"""
		Manifest 'name' considered source of truth for addonID
		Must match:
		- Submission file name '<addonID>/<version>.json'
		- `addonId` within the submission JSON data
	"""
	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	def test_valid(self):
		"""No error when manifest 'name', submission file path, and submission contents all agree.
		"""
		errors = list(
			validate.checkAddonId(self.manifest, VALID_SUBMISSION_JSON_FILE, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
			],
			errors
		)

	def test_invalidPath(self):
		""" Error when submission path does not include correct addon ID
		"""
		filename = os.path.join(TOP_DIR, "invalid")
		errors = list(
			validate.checkAddonId(self.manifest, filename, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				(  # invalidPathError
					"Submitted json file must be placed in a folder matching"
					f" the addonId/name '{self.manifest['name']}'"
				),
			],
			errors
		)

	def test_invalidJSONData(self):
		""" Error when submission does not include correct addonId
		"""
		invalidID = "invalid"
		self.submissionData['addonId'] = invalidID
		errors = list(
			validate.checkAddonId(self.manifest, VALID_SUBMISSION_JSON_FILE, self.submissionData)
		)

		self.assertEqual(
			[  # expected errors
				(  # idMismatchError
					"Submission data 'addonId' field does not match 'name' field"
					f" in addon manifest: {VALID_ADDON_ID} vs {invalidID}"
				)
			],
			errors
		)

	def test_invalidJSONDataAndPath(self):
		""" Error when submission does not include correct addonId and file path does not include the addonID
		"""
		expectedAddonId = "valid"
		self.manifest['name'] = expectedAddonId
		errors = list(
			validate.checkAddonId(self.manifest, VALID_SUBMISSION_JSON_FILE, self.submissionData)
		)

		self.assertEqual(
			[  # expected errors
				(  # submissionPathIncorrect
					f"Submitted json file must be placed in a folder matching the addonId/name '{expectedAddonId}'"
				),
				(  # idMismatch
					"Submission data 'addonId' field does not match 'name' field"
					f" in addon manifest: {expectedAddonId} vs {'fake'}"
				),
			],
			errors
		)


@dataclass
class VersionNumber:
	major: int = 0
	minor: int = 0
	patch: int = 0


class Validate_checkVersions(unittest.TestCase):
	"""Tests for the checkVersions function.

		The following are considered:
		- A: Submission file name '<addonID>/<version>.json'
		- B: `addonVersionNumber` field within the submission JSON data
		- C: `addonVersionName` field within the submission JSON data
		- D: Manifest addon version name

		Constraints:
		- The submission file name (A) must be a string representation of the `addonVersionNumber` field (B)
			(fully qualified) eg '21.3.0.json'
		- The `addonVersionName` field (C) must match the manifest version name (D)
		- The `addonVersionName` field can be parsed as 2 or 3 digits,
			which match the `addonVersionNumber` field (B)
	"""
	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()
		self.fileName = ""

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	@staticmethod
	def _getVersionString(version: VersionNumber):
		return f"{version.major}.{version.minor}.{version.patch}"

	def _setupVersions(
			self,
			submissionFileNameVer: str,
			versionNum: VersionNumber,
			versionName: str,
			manifestVersion: str
	):
		"""Mutate instance variables for testing convenience
		"""
		self.fileName = os.path.join(ADDON_SUBMISSIONS_DIR, VALID_ADDON_ID, f"{submissionFileNameVer}.json")
		self.submissionData["addonVersionNumber"]["major"] = versionNum.major
		self.submissionData["addonVersionNumber"]["minor"] = versionNum.minor
		self.submissionData["addonVersionNumber"]["patch"] = versionNum.patch
		self.submissionData["addonVersionName"] = versionName
		self.manifest["version"] = manifestVersion

	def test_valid(self):
		"""No error when:
			- manifest version matches submission addonVersionName
			- submission file name matches submission addonVersionNumber (fully qualified)
			- submission addonVersionName can be parsed and matches addonVersionNumber
		"""
		versionName = "13.6.5"
		self._setupVersions(
			submissionFileNameVer=versionName,
			versionNum=VersionNumber(13, 6, 5),
			versionName=versionName,
			manifestVersion=versionName
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual([], errors)

	def test_fileNameMustMatchVerNum(self):
		""" Error expected when fileName is not a fully qualified (trailing zero's included),
		dot separated representation of the addonVersionNumber: eg '21.3.0.json'
		"""
		versionName = "13.06"
		self._setupVersions(
			submissionFileNameVer=versionName,  # expect "13.6.0"
			versionNum=VersionNumber(13, 6),
			versionName=versionName,
			manifestVersion=versionName
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				'Submission filename and versionNumber mismatch error:'
				' versionNumberField: 13.6.0'
				' version from submission filename: 13.06'
				' expected submission filename: 13.6.0.json'
			],
			errors
		)

	def test_fileNameMustUseFullyQualifiedVersion(self):
		"""Error expected when fileName is not a fully qualified (trailing zero's included),
		dot separated representation of the addonVersionNumber: eg '21.3.0.json'
		"""
		versionName = "13.6"
		self._setupVersions(
			submissionFileNameVer=versionName,  # expect "13.6.0"
			versionNum=VersionNumber(13, 6),
			versionName=versionName,
			manifestVersion=versionName
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				'Submission filename and versionNumber mismatch error:'
				' versionNumberField: 13.6.0'
				' version from submission filename: 13.6'
				' expected submission filename: 13.6.0.json'
			],
			errors
		)

	def test_dateBasedVersionNameValid(self):
		""" Date based version in manifest is ok. Add-ons use this scheme.
		"""
		self._setupVersions(
			submissionFileNameVer='13.6.0',
			versionNum=VersionNumber(13, 6),
			versionName="13.06",
			manifestVersion="13.06"
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[],
			errors,
		)

	def test_dateBasedWithPatchVersionNameValid(self):
		""" Date based version in manifest is ok. Add-ons use this scheme.
		"""
		self._setupVersions(
			submissionFileNameVer='13.6.5',
			versionNum=VersionNumber(13, 6, 5),
			versionName="13.06.5",
			manifestVersion="13.06.5"
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[],
			errors
		)

	def test_unparseableVersionName(self):
		""" Error when versionName include characters unable to be parsed to numeric form.
		These situations will need to be considered manually.
		"""
		self._setupVersions(
			submissionFileNameVer='13.6.0',
			versionNum=VersionNumber(13, 6),
			versionName="13.06-NG",
			manifestVersion="13.06-NG"
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				(
					"Warning: submission data 'addonVersionName' and 'addonVersionNumber' "
					'mismatch.  Unable to parse: 13.06-NG and match with 13.6.0'
				)
			],
			errors
		)

	def test_nonNumericVersionName(self):
		""" Error when versionName include characters unable to be parsed to numeric form.
		These situations will need to be considered manually.
		"""
		versionName = "June Release '21"
		self._setupVersions(
			submissionFileNameVer='13.6.0',
			versionNum=VersionNumber(13, 6),
			versionName=versionName,
			manifestVersion=versionName
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				(
					"Warning: submission data 'addonVersionName' and 'addonVersionNumber' "
					"mismatch.  Unable to parse: June Release '21 and match with 13.6.0"
				)
			],
			errors
		)

	def test_versionNameMustMatchManifest(self):
		""" Ensure there is no mistake with the release submission, the submission addonVersionName must match
		the version field from the manifest.
		"""
		self._setupVersions(
			submissionFileNameVer="12.2.0",
			versionNum=VersionNumber(12, 2),
			versionName="12.2",
			manifestVersion="13.2"
		)
		errors = list(
			validate.checkVersions(self.manifest, self.fileName, self.submissionData)
		)
		self.assertEqual(
			[  # expected errors
				(
					"Submission data 'addonVersionName' field does not match 'version' field"
					" in addon manifest: 13.2 vs addonVersionName: 12.2"
				)
			],
			errors
		)


class Validate_outputResult(unittest.TestCase):

	def test_output_errorRaises(self):
		singleErrorGen = ("error string" for _ in range(1))
		with self.assertRaises(ValueError):
			validate.outputResult(singleErrorGen)

	def test_output_noError(self):
		noErrorGen = ("error string" for _ in range(0))
		validate.outputResult(noErrorGen)


class Validate_End2End(unittest.TestCase):

	class OpenUrlResult:
		def __init__(self, readFunc):
			self.read = readFunc
			self.code = 200
			self.headers = {
				"content-length": os.path.getsize(ADDON_PACKAGE)
			}

	def setUp(self) -> None:
		self.addonReader = open(ADDON_PACKAGE, 'rb')
		self.urlOpenResult = self.OpenUrlResult(self.addonReader.read)

	def tearDown(self) -> None:
		self.addonReader.close()

	@patch('_validate.validate.urllib.request.urlopen')
	def test_success(self, mock_urlopen):
		"""Run validate on a known good file.
		"""
		mock_urlopen.return_value = self.urlOpenResult
		errors = list(
			validate.validateSubmission(VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(list(errors), [])

	@patch('_validate.validate.urllib.request.urlopen')
	def test_downloadFailure(self, mock_urlopen):
		"""Unable to download addon
		"""
		self.urlOpenResult.code = 404  # add-on not found
		mock_urlopen.return_value = self.urlOpenResult
		errors = list(
			validate.validateSubmission(VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(
			list(errors),
			[
				'Download of addon failed',
				'Fatal error, unable to continue: Unable to download from '
				# note this the mocked urlopen function actually fetches from ADDON_PACKAGE
				'https://github.com/'
				'nvdaes/clipContentsDesigner/releases/download/13.0/'
				'clipContentsDesigner-13.0.nvda-addon, '
				'HTTP response status code: 404'
			]
		)


class ParseVersionString(unittest.TestCase):

	def test_single(self):
		self.assertEqual(
			{
				"major": 24,
				"minor": 0,
				"patch": 0,
			},
			validate.parseVersionStr("24")
		)

	def test_double(self):
		self.assertEqual(
			{
				"major": 24,
				"minor": 6,
				"patch": 0,
			},
			validate.parseVersionStr("24.6")
		)

	def test_triple(self):
		self.assertEqual(
			{
				"major": 24,
				"minor": 6,
				"patch": 1,
			},
			validate.parseVersionStr("24.6.1")
		)


class VersionRegex(unittest.TestCase):

	def test_versionMajorMinorPatch_valid(self):
		ver = "23.5.1"
		matches = validate.VERSION_PARSE.match(ver)
		self.assertTrue(matches)
		groups = list(x for x in matches.groups() if x)
		self.assertEqual(
			['23', '5', '1'],
			groups
		)

	def test_versionMajorMinor_valid(self):
		ver = "6.0"
		matches = validate.VERSION_PARSE.match(ver)
		self.assertTrue(matches)
		groups = list(x for x in matches.groups() if x)
		self.assertEqual(
			['6', '0'],
			groups
		)

	def test_versionMajor_valid(self):
		ver = "1"
		matches = validate.VERSION_PARSE.match(ver)
		self.assertTrue(matches)
		groups = list(x for x in matches.groups() if x)
		self.assertEqual(
			['1'],
			groups
		)

	def test_NonDotSep_invalid(self):
		ver = f"{3},{2},{1}"
		matches = validate.VERSION_PARSE.match(ver)
		self.assertFalse(matches)
