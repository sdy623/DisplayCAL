/* ############################## */
/* ##### jsapi Distribution ##### */
/* ############################## */

/* ##### Array.prototype.pop.js ##### */

/*
	2006 Ash Searle
	
	http://hexmen.com/blog/2006/12/push-and-pop/
*/

if (!Array.prototype.pop) Array.prototype.pop = function() {
	// Removes the last element from an array and returns that element. This method changes the length of the array.
	var n = this.length >>> 0, value;
	if (n) {
		value = this[--n];
		delete this[n]
	};
	this.length = n;
	return value
};

if (!Array.pop) Array.pop = function(object) {
	return Array.prototype.pop.apply(object)
};

/* ##### Array.prototype.shift.js ##### */

/*
	2006 Florian Hoech
	
	Array.prototype.shift.js
	
	adds shift method for arrays in browsers without native or incorrect implementation
*/

if (!Array.prototype.shift) Array.prototype.shift = function() {
	// Removes the first element from an array and returns that element. This method changes the length of the array.
	var n = this.length >>> 0, value = this[0];
	for (var i = 1; i < n; i ++) this[i - 1] = this[i];
	delete this[n];
	this.length = n - 1 >>> 0;
	return value
};

if (!Array.shift) Array.shift = function(object) {
	return Array.prototype.shift.apply(object)
};

/* ##### Array.prototype.unshift.js ##### */

/*
	2006 Florian Hoech
	
	Array.prototype.unshift.js
	
	adds unshift method for arrays in browsers without native or incorrect implementation
*/

if (!Array.prototype.unshift) Array.prototype.unshift = function() {
	// Adds one or more elements to the beginning of an array and returns the new length of the array.
	var n = this.length >>> 0;
	for (var i = (n - 1) >>> 0; i >= 0; i --) this[i + arguments.length] = this[i];
	for (var i = arguments.length - 1; i >= 0; i --) {
		this[i] = arguments[i];
		n = n + 1 >>> 0
	};
	this.length = n;
	return n
};

/* ##### Array.prototype.push.js ##### */

/*
	2006 Ash Searle
	
	http://hexmen.com/blog/2006/12/push-and-pop/
*/

if (!Array.prototype.push || [].push(0) == 0) Array.prototype.push = function() {
	var n = this.length >>> 0;
	for (var i = 0; i < arguments.length; i++) {
		this[n] = arguments[i];
		n = n + 1 >>> 0
	};
	this.length = n;
	return n
};

/* ##### Array.prototype.splice.js ##### */

/*
	2006 Florian Hoech
	
	Array.prototype.splice.js
	
	adds splice method for arrays in browsers without native or incorrect implementation
*/

if (!Array.prototype.splice || [0].splice(0, 1) === 0) Array.prototype.splice = function(index, howMany) {
	/*
		Changes the content of an array, adding new elements while removing old elements.
		Returns an array containing the removed elements. If only one element is removed, an array of one element is returned.
		Returns undefined if no arguments are passed.
	*/
	if (arguments.length == 0) return index;
	if (typeof index != "number") index = 0;
	if (index < 0) index = Math.max(0, this.length + index);
	if (index > this.length) {
		if (arguments.length > 2) index = this.length;
		else return []
	};
	if (arguments.length < 2) howMany = this.length - index;
	howMany = (typeof howMany == "number") ? Math.max(0, howMany) : 0;
	var removedElements = this.slice(index, index + howMany);
	var elementsToMove = this.slice(index + howMany);
	this.length = index;
	for (var i = 2; i < arguments.length; i ++) this[this.length] = arguments[i];
	for (var i = 0; i < elementsToMove.length; i ++) this[this.length] = elementsToMove[i];
	return removedElements
};

/* ##### Number.prototype.toFixed.js ##### */

/*
	2006 Florian Hoech
	
	Number.prototype.toFixed.js
*/

if (!Number.prototype.toFixed) {
	Number.prototype.toFixed = function(ln) {
		if (!ln) ln = 0;
		var i, n = Math.pow(10, ln),
			n = (Math.round(this * n) / n) + "";
		if (ln && (i = n.indexOf(".")) < 0) {
			i = n.length;
			n += "."
		};
		while (n.substr(i).length < ln + 1) n += "0";
		return n
	}
};

/* ##### jsapi.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.js</file>
	</jsapi>
*/

jsapi = function() {
	return new jsapi.jsapi(arguments);
};
jsapi.constants = {
	OBJECTTYPES: {
		OBJECT: 0,
		ARRAY: 1,
		BOOLEAN: 2,
		DATE: 3,
		FUNCTION: 4,
		NUMBER: 5,
		REGEXP: 6,
		STRING: 7
	}
};
jsapi.extend = function(object, _this) {
	jsapi.jsapi.prototype.extend(object, _this)
};
jsapi.jsapi = function() {
	var objectType;
	if (!jsapi.initialized) {
		for (var propertyName in jsapi.dom) if (typeof jsapi.dom[propertyName] == "function" && !jsapi.dom[propertyName]._args) jsapi.dom[propertyName]._args = [jsapi.dom.isNode];
		for (var propertyName in jsapi.regexp) if (typeof jsapi.regexp[propertyName] == "function") jsapi.regexp[propertyName]._args = [function(argument) {
			return argument instanceof RegExp;
		}];
		for (var propertyName in jsapi.string) if (typeof jsapi.string[propertyName] == "function") jsapi.string[propertyName]._args = [function(argument) {
			return typeof argument == "string" || argument instanceof String;
		}];
		for (var propertyName in jsapi) jsapi.extend(jsapi[propertyName], jsapi[propertyName]);
		var arrayMethodNames = [
			"every",
			"filter",
			"forEach",
			"indexOf",
			"join",
			"lastIndexOf",
			"map",
			"slice",
			"some",
			/* Mutator methods */
			"pop",
			"push",
			"reverse",
			"shift",
			"sort",
			"splice",
			"unshift"
		];
		for (var i = 0; i < arrayMethodNames.length; i ++) {
			(function (arrayMethodName) {
				jsapi.jsapi.prototype[arrayMethodName] = function () {
					var result = Array.prototype[arrayMethodName].apply(this, arguments);
					return typeof result == "object" ? jsapi(result) : (result != null || arrayMethodName == "pop" || arrayMethodName == "shift" ? result : this);
				}
			})(arrayMethodNames[i]);
		};
		jsapi.initialized = true;
	};
	if (this.length == null) this.length = 0;
	for (var i = 0; i < arguments[0].length; i ++) {
		var object = arguments[0][i];
		switch (typeof object) {
			case "function":
				objectType = jsapi.constants.OBJECTTYPES.FUNCTION;
				break;
			case "number":
				objectType = jsapi.constants.OBJECTTYPES.NUMBER;
				break;
			case "string":
				objectType = jsapi.constants.OBJECTTYPES.STRING;
				break;
			default:
				if (!object) continue; // null or undefined
				switch (object.constructor) {
					case Boolean:
						objectType = jsapi.constants.OBJECTTYPES.BOOLEAN;
						break;
					case Date:
						objectType = jsapi.constants.OBJECTTYPES.DATE;
						break;
					case Number:
						objectType = jsapi.constants.OBJECTTYPES.NUMBER;
						break;
					case RegExp:
						objectType = jsapi.constants.OBJECTTYPES.REGEXP;
						break;
					case String:
						objectType = jsapi.constants.OBJECTTYPES.STRING;
						break;
					default:
						objectType = jsapi.constants.OBJECTTYPES.OBJECT;
				}
		};
		switch (objectType) {
			case jsapi.constants.OBJECTTYPES.STRING:
				var expression = object.split(":");
				if (expression.length > 1) switch (expression[0]) {
					case "html":
					case "xhtml":
					case "xml":
						object = jsapi.dom.parseString(expression.slice(1).join(":"));
						break;
					case "xpath":
						object = jsapi.dom.getByXpath(expression.slice(1).join(":"));
						break;
				}
				else if (/<[^<]*>/.test(object)) object = jsapi.dom.parseString(object);
			default:
				if (object instanceof Array) Array.prototype.push.apply(this, object);
				else if (typeof object == "object" && typeof object.length == "number" && object.constructor != String && object.constructor != Function) 
					Array.prototype.push.apply(this, Array.prototype.slice.apply(object));
				else this[this.length ++] = object;
		}
	};
};
jsapi.jsapi.prototype = {
	concat: function(object) {
		var result = jsapi(this);
		jsapi.jsapi.apply(result, [object]);
		return result
	},
	extend: function(object, _this) {
		/*
			if _this evaluates to false, use the current result as "this"-object.
			otherwise, use _this as "this"-object and pass the current result as first argument.
		*/
		for (var propertyName in object) if (typeof object[propertyName] == "function" && 
			propertyName != "$" && 
			propertyName != "extend" && 
			propertyName != "toString" && 
			propertyName != "valueOf") {
			if (!this[propertyName]) {
				this[propertyName] = function() {
					if (this.length) {
						var _callbacks = arguments.callee._callbacks;
						for (var i = 0; i < this.length; i ++) {
							for (var n = 0; n < _callbacks.length; n ++) {
								var _this = _callbacks[n]._this || this[i],
									_arguments = _callbacks[n]._this ? [this[i]].concat(Array.prototype.slice.apply(arguments)) : arguments;
								if (_callbacks[n].hasValidArguments.apply(_callbacks[n], _arguments)) {
									this[i] = _callbacks[n].apply(_this, _arguments);
								}
							}
						}
					};
					return this;
				};
				this[propertyName]._callbacks = [];
			};
			if (!object[propertyName].hasValidArguments) {
				if (object[propertyName]._args) object[propertyName].hasValidArguments = function() {
					for (var i = 0; i < this._args.length; i ++) {
						if (!(typeof this._args[i] == "string" ? 
							typeof arguments[i] == this._args[i] : 
							(typeof this._args[i] == "function" ? 
								this._args[i](arguments[i]) : 
								arguments[i] == this._args[i]))) {
									return false;
						}
					};
					return true
				};
				else object[propertyName].hasValidArguments = function() { return true };
			};
			object[propertyName]._this = _this;
			if (this[propertyName]._callbacks.indexOf(object[propertyName]) < 0) this[propertyName]._callbacks.push(object[propertyName]);
		}
	},
	toString: function() {
		return Array.prototype.slice.apply(this).toString();
	}
};

/* ##### jsapi.array.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.array.js</file>
		<dependencies>
			jsapi.js
		</dependencies>
	</jsapi>
*/

	jsapi.array = {
		$: function(object) {
			// make array from object with only the numerical indices
			var array = [], n;
			if (object.length != null) for (var i = 0; i < object.length; i ++) array[i] = object[i];
			else for (var i in object) if (!isNaN(n = parseInt(i)) && n == i) array[n] = object[i];
			return array
		}
	};
	jsapi.array.$._args = [null];

/* ##### jsapi.array.flat.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.array.search.js</file>
		<dependencies>
			jsapi.array.js
		</dependencies>
	</jsapi>
*/

	jsapi.array.flat = function(a) {
		var r = [];
		for (var i = 0; i < a.length; i ++) {
			if (a[i].constructor == Array) r = r.concat(jsapi.array.flat(a[i]));
			else r.push(a[i])
		};
		return r
	};
	jsapi.array.flat._args = [Array];

/* ##### jsapi.dom.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.js</file>
		<dependencies>
			jsapi.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom = {};

/* ##### jsapi.dom.NODETYPES.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.NODETYPES.js</file>
		<dependencies>
			jsapi.dom.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom.NODETYPES = {
		"1": "ELEMENT",
		"2": "ATTRIBUTE",
		"3": "TEXT",
		"4": "CDATA_SECTION",
		"5": "ENTITY_REFERENCE",
		"6": "ENTITY",
		"7": "PROCESSING_INSTRUCTION",
		"8": "COMMENT",
		"9": "DOCUMENT",
		"10": "DOCUMENT_TYPE",
		"11": "DOCUMENT_FRAGMENT",
		"12": "NOTATION"
	};

/* ##### jsapi.dom.isNode.js ##### */

/*
	<jsapi>
		<author>Florian Hoech</author>
		<file>jsapi.dom.isNode.js</file>
		<dependencies>
			jsapi.dom.NODETYPES.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom.isNode = function(object) {
		return !!(object && jsapi.dom.NODETYPES[object.nodeType] && object.cloneNode);
	};

/* ##### jsapi.string.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.string.js</file>
		<dependencies>
			jsapi.js
		</dependencies>
	</jsapi>
*/

	jsapi.string = {};

/* ##### jsapi.string.trim.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.string.trim.js</file>
		<dependencies>
			jsapi.string.js
		</dependencies>
	</jsapi>
*/

	jsapi.string.trim = function(str) {
		return str.replace(/(^\s+|\s+$)/g, "")
	};
	jsapi.string.trim._args = [String];

/* ##### jsapi.useragent.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.useragent.js</file>
		<dependencies>
			jsapi.string.trim.js
		</dependencies>
	</jsapi>
		
	TO-DO: add KHTML
*/

	jsapi.useragent = {
		$: function (ua) {
			ua = (ua || navigator.userAgent).toLowerCase();
			var i, j, match, _match, replace = [
				[/(\d+\.)(\d+)\.(\d+)(\.(\d+))?/g, "$1$2$3$5"],
				[/linux/g, ";linux;linux"],
				[/mac/, ";mac;mac"],
				[/microsoft ((p)ocket )?internet explorer/g, "ms$2ie"],
				[/win32/g, "windows"],
				[/windows (\w+)/g, "windows;windows $1"]
			];
			for (i = 0; i < replace.length; i ++) ua = ua.replace(replace[i][0], replace[i][1]);
			ua = ua.split(/[\(\)\[\]\{\}\,;]/);
			for (i in this) {
				if (typeof this[i] != "object" && typeof this[i] != "function") delete this[i]
			};
			for (i = 0; i < ua.length; i ++) {
				match = ua[i].match(/[a-z\.\-_]+(\s+[a-z\.\-_]+)*\Wv?\d+(\.\d+)*/g);
				if (match) {
					for (j = 0; j < match.length; j ++) {
						_match = match[j].match(/([a-z\.\-_]+(\s[a-z\.\-_]+)*)\Wv?(\d+(\.\d+)*)/);
						if (!this[_match[1]] || (parseFloat(_match[3]) == _match[3] && this[_match[1]] < parseFloat(_match[3]))) this[_match[1]] = parseFloat(_match[3]) == _match[3] ? parseFloat(_match[3]) : _match[3]
					}
				}
				else {
					ua[i] = jsapi.string.trim(ua[i]);
					if (ua[i]) this[ua[i]] = true
				}
			};
			if (this.konqueror && !this.khtml) this.khtml = true;
			if (this.safari === true) delete this.safari; // safari would have a version number here
			if (!this.gecko && this.mozilla) {
				this.compatible = this.mozilla;
				delete this.mozilla
			};
			if (this.opera || this.safari || this.konqueror) {
				if (this.mozilla) delete this.mozilla;
				if (this.msie) delete this.msie
			};
			return this
		}
	};
	jsapi.useragent.toString = function() {
		var props = [];
		for (i in this) {
			if (typeof this[i] != "object" && typeof this[i] != "function")
props.push((/\s/.test(i) ? "'" : "") + i + (/\s/.test(i) ? "'" : "") + ":" + (typeof this[i] == "string" ? '"' : "") + this[i] + (typeof this[i] == "string" ? '"' : ""))
		};
		return props.join(", ");
	};
	jsapi.useragent.$._args = [String];
	jsapi.useragent.$();

/* ##### jsapi.util.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.util.js</file>
		<dependencies>
			jsapi.js
		</dependencies>
	</jsapi>
*/

	jsapi.util = {};

/* ##### jsapi.generic_accessor_mutator.js ##### */

/*
	<jsapi>
		<author>Florian Hoech</author>
		<file>jsapi.generic_accessor_mutator.js</file>
		<dependencies>
			jsapi.js
			jsapi.dom.js
			jsapi.dom.isNode.js
			jsapi.useragent.js
			jsapi.util.js
		</dependencies>
	</jsapi>
*/

	jsapi.constants.ATTRIBUTE_ALIASES = {
		"class": "className",
		"for": "htmlFor",
		readonly: "readOnly",
		maxlength: "maxLength"
	};
	jsapi._attribute = function(object, attributeName, value) { // if arguments.length == 2, get attribute. otherwise, if value == null, remove attribute, else set attribute
		switch (attributeName) {
			case "style":
			case "value":
				return arguments.length == 2 ? jsapi._property(object, attributeName) : jsapi._property(object, attributeName, value);
			default:
				if (jsapi.constants.ATTRIBUTE_ALIASES[attributeName]) return jsapi._property.apply(jsapi, arguments);
				else {
					if (arguments.length == 2) return object.getAttribute(attributeName); // get attribute
					if (value == null) object.removeAttribute(attributeName); // remove attribute
					else object.setAttribute(attributeName, value); // set attribute
				}
		};
		return object
	};
	jsapi._property = function(object, propertyName, value) { // if arguments.length == 2, get property. otherwise, if value == null, delete property, else set property
		switch (propertyName) {
			case "style":
				if (arguments.length == 2) return object.style.cssText; // get attribute
				object.style.cssText = value || ""; // set attribute
				break;
		};
		if (jsapi.dom.isNode(object)) propertyName = jsapi.constants.ATTRIBUTE_ALIASES[propertyName] || propertyName;
		if (arguments.length == 2) return object[propertyName];
		object[propertyName] = value; // set property
		if (value == null) try { delete object[propertyName] } catch (e) {  }; // delete property
		return object
	};
	jsapi.dom.attr =
	jsapi.dom.attribute = function (object, attribute, value) {
		return arguments.length == 2 && (typeof attribute != "object" || attribute instanceof Array) ? jsapi._get(object, jsapi._attribute, attribute) : jsapi._set(object, jsapi._attribute, attribute, value);
	};
	jsapi.util.prop = 
	jsapi.util.property = function (object, property, value) {
		return arguments.length == 2 && (typeof property != "object" || property instanceof Array) ? jsapi._get(object, jsapi._property, property) : jsapi._set(object, jsapi._property, property, value);
	};
	jsapi._get = function (object, callback, property) {
		if (typeof property != "object") return callback(object, property);
		else {
			var result = [];
			for (var i = 0; i < property.length; i ++) result.push(callback(object, property[i]));
			return result;
		}
	};
	jsapi._set = function (object, callback, property, value) {
		if (typeof property != "object") callback(object, property, value);
		else {
			if (property instanceof Array) for (var i = 0; i < property.length; i ++) callback(object, property[i], value);
			else for (var propertyName in property) callback(object, propertyName, property[propertyName] != null ? property[propertyName] : value);
		};
		return object;
	};;

/* ##### jsapi.dom.attribute.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.attribute.js</file>
		<dependencies>
			jsapi.generic_accessor_mutator.js
		</dependencies>
	</jsapi>
*/


/* ##### jsapi.dom.attributeAddWord.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.attributeAddWord.js</file>
		<dependencies>
			jsapi.dom.attribute.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom.attributeAddWord = function(element, attr, word) {
		var value = jsapi.dom.attribute(element, attr);
		return jsapi.dom.attribute(element, attr, (value != null ? value + " " : "") + word)
	};

/* ##### jsapi.dom.attributeHasWord.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.attributeHasWord.js</file>
		<dependencies>
			jsapi.dom.attribute.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom.attributeHasWord = function(element, attr, word) {
		return (new RegExp("(^|\\s)" + word + "(\\s|$)")).test(jsapi.dom.attribute(element, attr))
	};

/* ##### jsapi.dom.attributeRemoveWord.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.dom.attributeRemoveWord.js</file>
		<dependencies>
			jsapi.dom.attribute.js
		</dependencies>
	</jsapi>
*/

	jsapi.dom.attributeRemoveWord = function(element, attr, word) {
		var value = jsapi.dom.attribute(element, attr);
		if (value) jsapi.dom.attribute(element, attr, value.replace(new RegExp("(^|\\s+)" + word + "(\\s|$)"), "$2"));
		return element
	};

/* ##### jsapi.math.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.math.js</file>
		<dependencies>
			jsapi.array.flat.js
		</dependencies>
	</jsapi>
*/

	jsapi.math = {
		absmax: function(v) {
			var a = jsapi.array.flat(arguments), r = 0;
			for (var i = 0; i < a.length; i ++) if (Math.abs(r) < Math.abs(a[i])) r = a[i];
			return r
		},
		avg: function() {
			var a = jsapi.array.flat(arguments), r = 0;
			for (var i = 0; i < a.length; i ++) r += a[i];
			return r / a.length
		},
		cbrt: function(x) {
			return x >= 0 ? Math.pow (x, 1 / 3) : -Math.pow (-x, 1 / 3)
		},
		deg: function(v) {
			return v * 180 / Math.PI
		},
		longToUnsigned: function(num) {
			while (num < 0) num += 4294967296;
			return num
		},
		max: function(v) {
			var a = jsapi.array.flat(arguments), r = 0;
			for (var i = 0; i < a.length; i ++) r = Math.max(r, a[i]);
			return r
		},
		min: function(v) {
			var a = jsapi.array.flat(arguments), r = 0;
			for (var i = 0; i < a.length; i ++) r = Math.min(r, a[i]);
			return r
		},
		rad: function(v) {
			return v / 180 * Math.PI
		}
	};
	jsapi.math.absmax._args = [Number];
	jsapi.math.avg._args = [Number];
	jsapi.math.cbrt._args = [Number];
	jsapi.math.deg._args = [Number];
	jsapi.math.longToUnsigned._args = [Number];
	jsapi.math.max._args = [Array];
	jsapi.math.min._args = [Array];
	jsapi.math.rad._args = [Number];

/* ##### jsapi.math.color.js ##### */

/*
	<jsapi>
		<author>2006 Florian Hoech</author>
		<file>jsapi.math.color.js</file>
		<dependencies>
			jsapi.math.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color = {};

/* ##### jsapi.math.color.CIEDCorColorTemp2xyY.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.CIEDCorColorTemp2xyY.js</file>
		<dependencies>
			jsapi.math.color.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.CIEDCorColorTemp2xyY = function(T, scaleY) {
		// derived from formula found on www.brucelindbloom.com
		if (typeof T == "string") switch (T.toUpperCase()) {
			case "B":	// direct sunlight
				T = 4875;
				break;
			case "C":	// covered sky daylight
				T = 6774;
				break;
			case "D50":
				T = 5000;
				break;
			case "D55":
				T = 5500;
				break;
			case "D65":
				T = 6504;
				break;
			case "D75":
				T = 7500;
				break;
			default:
				T = 0;
		};
		var xD = 4000 <= T && T <= 7000
			? ((-4.607 * Math.pow(10, 9)) / Math.pow(T, 3))
				+ ((2.9678 * Math.pow(10, 6)) / Math.pow(T, 2))
				+ ((0.09911 * Math.pow(10, 3)) / T)
				+ 0.244063
			: (7000 < T && T <= 25000 
				? ((-2.0064 * Math.pow(10, 9)) / Math.pow(T, 3))
							+ ((1.9018 * Math.pow(10, 6)) / Math.pow(T, 2))
							+ ((0.24748 * Math.pow(10, 3)) / T)
							+ 0.237040
				: null),
			yD = xD != null ? -3 * Math.pow(xD, 2) + 2.87 * xD - 0.275 : null;
		return xD == null ? null : [xD, yD, scaleY ? 100 : 1];
	};

/* ##### jsapi.math.color.xyY2XYZ.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.xyY2XYZ.js</file>
		<dependencies>
			jsapi.math.color.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.xyY2XYZ = function(x, y, Y, scale) {
		if (Y > 1) Y = Y / 100;
		var X = (x * Y) / y,
			Y = Y,
			Z = (1 - x - y) * Y / y,
			s = scale ? 100 : 1;
		return [X * s, Y * s, Z * s];
	};

/* ##### jsapi.math.color.CIEDCorColorTemp2XYZ.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.CIEDCorColorTemp2XYZ.js</file>
		<dependencies>
			jsapi.math.color.CIEDCorColorTemp2xyY.js
			jsapi.math.color.xyY2XYZ.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.CIEDCorColorTemp2XYZ = function(T, scale) {
		var xyY = jsapi.math.color.CIEDCorColorTemp2xyY(T, scale);
		return jsapi.math.color.xyY2XYZ(xyY[0], xyY[1], xyY[2], scale);
	};

/* ##### jsapi.math.color.Lab2XYZ.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.Lab2XYZ.js</file>
		<dependencies>
			jsapi.math.color.CIEDCorColorTemp2XYZ.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.Lab2XYZ = function(L, a, b, whitepoint) {
		// based on http://www.easyrgb.com/math.php?MATH=M8
		// whitepoint can be a color temperature in Kelvin or an array containing XYZ values
		var var_Y = ( L + 16 ) / 116;
		var var_X = a / 500 + var_Y;
		var var_Z = var_Y - b / 200;
		
		if ( Math.pow(var_Y, 3) > 0.008856 ) var_Y = Math.pow(var_Y, 3);
		else                      var_Y = ( var_Y - 16 / 116 ) / 7.787;
		if ( Math.pow(var_X, 3) > 0.008856 ) var_X = Math.pow(var_X, 3);
		else                      var_X = ( var_X - 16 / 116 ) / 7.787;
		if ( Math.pow(var_Z, 3) > 0.008856 ) var_Z = Math.pow(var_Z, 3);
		else                      var_Z = ( var_Z - 16 / 116 ) / 7.787;
		
		var ref_XYZ = whitepoint ? (whitepoint.constructor == Array ? whitepoint : jsapi.math.color.CIEDCorColorTemp2XYZ(whitepoint, true)) : [95.047, 100.000, 108.883]; // Observer= 2°, Illuminant= D65
		
		var X, Y, Z;
		X = ref_XYZ[0] * var_X;
		Y = ref_XYZ[1] * var_Y;
		Z = ref_XYZ[2] * var_Z;
		
		return [X, Y, Z]
	};

/* ##### jsapi.math.color.XYZ2rgb.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.XYZ2rgb.js</file>
		<dependencies>
			jsapi.math.color.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.XYZ2rgb = function(X, Y, Z) {
		// http://www.easyrgb.com/math.php?MATH=M1
		//Observer = 2°, Illuminant = D65
		var var_X = X / 100;        //Where X = 0 ÷  95.047
		var var_Y = Y / 100;        //Where Y = 0 ÷ 100.000
		var var_Z = Z / 100;        //Where Z = 0 ÷ 108.883
		
		var var_R = var_X *  3.2406 + var_Y * -1.5372 + var_Z * -0.4986;
		var var_G = var_X * -0.9689 + var_Y *  1.8758 + var_Z *  0.0415;
		var var_B = var_X *  0.0557 + var_Y * -0.2040 + var_Z *  1.0570;
		
		// sRGB gamma function
		if ( var_R > 0.0031308 ) var_R = 1.055 * Math.pow( var_R, 1 / 2.4 ) - 0.055;
		else                     var_R = 12.92 * var_R;
		if ( var_G > 0.0031308 ) var_G = 1.055 * Math.pow( var_G, 1 / 2.4 ) - 0.055;
		else                     var_G = 12.92 * var_G;
		if ( var_B > 0.0031308 ) var_B = 1.055 * Math.pow( var_B, 1 / 2.4 ) - 0.055;
		else                     var_B = 12.92 * var_B;
		
		var R, G, B;
		R = Math.max(0, Math.round(var_R * 255)); // avoid negative values through Math.max(0, R)
		G = Math.max(0, Math.round(var_G * 255)); // avoid negative values through Math.max(0, G)
		B = Math.max(0, Math.round(var_B * 255)); // avoid negative values through Math.max(0, B)
		
		return [R, G, B]
	};

/* ##### jsapi.math.color.Lab2rgb.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.Lab2rgb.js</file>
		<dependencies>
			jsapi.math.color.Lab2XYZ.js
			jsapi.math.color.XYZ2rgb.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.Lab2rgb = function(L, a, b, whitepoint) {
		var XYZ;
		XYZ = jsapi.math.color.Lab2XYZ(L, a, b, whitepoint);
		return jsapi.math.color.XYZ2rgb(XYZ[0], XYZ[1], XYZ[2])
	};

/* ##### jsapi.math.color.XYZ2Lab.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.XYZ2Lab.js</file>
		<dependencies>
			jsapi.math.js
			jsapi.math.color.CIEDCorColorTemp2xyY.js
			jsapi.math.color.xyY2XYZ.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.XYZ2Lab = function(X, Y, Z, Xr, Yr, Zr) {
		/*
			based on formula from www.brucelindbloom.com
			Xr, Yr, Zr = reference whitepoint -or- Xr = reference color temperature in Kelvin
		*/
		if (Yr == null || Zr == null) {
			if (Xr == null) Xr = "D50";
			if (typeof Xr == "string") {
				switch (Xr.toUpperCase()) {
					case "A":	// light bulb, 2856K
						Xr = 109.828;
						Yr = 35.547;
						break;
					case "B":	// direct sunlight, 4875K
						Xr = 99.072;
						Yr = 85.223;
						break;
					case "C":	// covered sky daylight, 6774K
						Xr = 98.041;
						Yr = 118.103;
						break;
					case "D55":
						Xr = 95.642;
						Zr = 92.085;
						break;
					case "D65":
						Xr = 95.0467;
						Yr = 108.8969;
						break;
					case "D75":
						Xr = 94.939;
						Yr = 122.558;
						break;
					case "E":
						Xr = 100;
						Yr = 100;
						break;
					default:	// D50, 5000K
						Xr = 96.422;
						Zr = 82.521;
				};
				Yr = 100;
			}
			else {
				var xyY = jsapi.math.color.CIEDCorColorTemp2xyY(Xr, true);
				var XYZ = jsapi.math.color.xyY2XYZ(xyY[0], xyY[1], xyY[2]);
				Xr = XYZ[0];
				Yr = XYZ[1];
				Zr = XYZ[2];
			}
		};
		var E = 216/24389,
			K = 24389/27,
			xr = X / Xr,
			yr = Y / Yr,
			zr = Z / Zr,
			fx = xr > E ? jsapi.math.cbrt(xr) : (K * xr + 16) / 116,
			fy = yr > E ? jsapi.math.cbrt(yr) : (K * yr + 16) / 116,
			fz = zr > E ? jsapi.math.cbrt(zr) : (K * zr + 16) / 116,
			L = 116 * fy - 16,
			a = 500 * (fx - fy),
			b = 200 * (fy - fz);
		return [L, a, b];
	};

/* ##### jsapi.math.color.delta.js ##### */

/*
	<jsapi>
		<author>2007 Florian Hoech</author>
		<file>jsapi.math.color.delta.js</file>
		<dependencies>
			jsapi.math.color.js
		</dependencies>
	</jsapi>
*/

	jsapi.math.color.delta = function (L1, a1, b1, L2, a2, b2, method, p1, p2, p3, debug) {
		/*
			CIE 1994 & CMC calculation code derived from formulas on www.brucelindbloom.com
			CIE 1994 code uses some alterations seen on www.farbmetrik-gall.de/cielab/korrcielab/cie94.html (see notes in code below)
			CIE 2000 calculation code derived from Excel spreadsheet available at www.ece.rochester.edu/~gsharma/ciede2000
			
			method: either "CIE94", "CMC", "CIE2K" or "CIE76" (default if method is not set)
			
			p1, p2, p3 arguments have different meaning for each calculation method:
			
				CIE 1994: if p1 is not null, calculation will be adjusted for textiles, otherwise graphics arts (default if p1 is not set)
				CMC(l:c): p1 equals l (lightness) weighting factor and p2 equals c (chroma) weighting factor.
					commonly used values are CMC(1:1) for perceptability (default if p1 and p2 are not set) and CMC(2:1) for acceptability
				CIE 2000: p1 becomes kL (lightness) weighting factor, p2 becomes kC (chroma) weighting factor and p3 becomes kH (hue) weighting factor
					(all three default to 1 if not set)
		*/
		for (i = 0; i < 6; i ++) if (typeof arguments[i] != "number" || isNaN(arguments[i])) return NaN;
		if (typeof method == "string") method = method.toLowerCase();
		switch (method) {
			case "94":
			case "1994":
			case "cie94":
			case "cie1994":
				var textiles = p1,
					dL = L1 - L2,
					C1 = Math.sqrt(Math.pow(a1, 2) + Math.pow(b1, 2)),
					C2 = Math.sqrt(Math.pow(a2, 2) + Math.pow(b2, 2)),
					dC = C1 - C2,
					da = a1 - a2,
					db = b1 - b2,
					dH = Math.sqrt(Math.round((Math.pow(da, 2) + Math.pow(db, 2) - Math.pow(dC, 2))*100000000000000)/100000000000000),
					// this is merely a bugfix for browser quirks experienced in mozilla:
					//dH = isNaN(dH) ? Math.sqrt(Math.pow(da, 2) + Math.pow(db, 2) - Math.round(Math.pow(dC, 2)*100000000000000)/100000000000000) : dH,
					// --
					SL = 1,
					K1 = textiles ? 0.048 : 0.045,
					K2 = textiles ? 0.014 : 0.015,
					C_ = (Math.sqrt((1 + (K1 * C1)) * (1 + (K1 * C2))) - 1) / K1, // www.farbmetrik-gall.de/cielab/korrcielab/cie94.html
					SC = 1 + K1 * C_, // brucelindbloom.com formula originally used C1 instead of C_, but the results are different from ProfileMaker/MeasureTool implementation, so use this instead (found on www.farbmetrik-gall.de/cielab/korrcielab/cie94.html)
					SH = 1 + K2 * C_, // brucelindbloom.com formula originally used C1 instead of C_, but the results are different from ProfileMaker/MeasureTool implementation, so use this instead (found on www.farbmetrik-gall.de/cielab/korrcielab/cie94.html)
					KL = textiles ? 2 : 1,
					KC = 1,
					KH = 1,
					dE = Math.sqrt(Math.pow(dL / (KL * SL), 2) + Math.pow(dC / (KC * SC), 2) + Math.pow(dH / (KH * SH), 2));
				break;
			case "cmc(2:1)":
			case "cmc21":
				p1 = 2;
			case "cmc(1:1)":
			case "cmc11":
			case "cmc":
				var l = typeof p1 == "number" ? p1 : 1,
					c = typeof p2 == "number" ? p2 : 1;
					dL = L1 - L2,
					C1 = Math.sqrt(Math.pow(a1, 2) + Math.pow(b1, 2)),
					C2 = Math.sqrt(Math.pow(a2, 2) + Math.pow(b2, 2)),
					dC = C1 - C2,
					da = a1 - a2,
					db = b1 - b2,
					dH = Math.sqrt(Math.round((Math.pow(da, 2) + Math.pow(db, 2) - Math.pow(dC, 2))*100000000000000)/100000000000000),
					// this is merely a bugfix for browser quirks experienced in mozilla:
					//dH = isNaN(dH) ? Math.sqrt(Math.pow(da, 2) + Math.pow(db, 2) - Math.round(Math.pow(dC, 2)*100000000000000)/100000000000000) : dH,
					// --
					SL = L1 < 16 ? 0.511 : (0.040975 * L1) / (1 + 0.01765 * L1),
					SC = (0.0638 * C1) / (1 + 0.0131 * C1) + 0.638,
					F = Math.sqrt(Math.pow(C1, 4) / (Math.pow(C1, 4) + 1900)),
					H1 = jsapi.math.deg(Math.atan2(b1, a1)) + (b1 >= 0 ? 0 : 360),
					T = 164 <= H1 && H1 <= 345 ? 0.56 + Math.abs(0.2 * Math.cos(jsapi.math.rad(H1 + 168))) : 0.36 + Math.abs(0.4 * Math.cos(jsapi.math.rad(H1 + 35))),
					SH = SC * (F * T + 1 - F),
					dE = Math.sqrt(Math.pow(dL / (l * SL), 2) + Math.pow(dC / (c * SC), 2) + Math.pow(dH / SH, 2));
				break;
			case "00":
			case "2k":
			case "2000":
			case "cie00":
			case "cie2k":
			case "cie2000":
				var pow25_7 = Math.pow(25, 7),
					k_L = typeof p1 == "number" ? p1 : 1,
					k_C = typeof p2 == "number" ? p2 : 1,
					k_H = typeof p3 == "number" ? p3 : 1,
					C1 = Math.sqrt(Math.pow(a1, 2) + Math.pow(b1, 2)),
					C2 = Math.sqrt(Math.pow(a2, 2) + Math.pow(b2, 2))	,
					C_avg = jsapi.math.avg(C1, C2),
					G = .5 * (1 - Math.sqrt(Math.pow(C_avg, 7) / (Math.pow(C_avg, 7) + pow25_7))),
					L1_ = L1,
					a1_ = (1 + G) * a1,
					b1_ = b1,
					L2_ = L2,
					a2_ = (1 + G) * a2,
					b2_ = b2,
					C1_ = Math.sqrt(Math.pow(a1_, 2) + Math.pow(b1_, 2)),
					C2_ = Math.sqrt(Math.pow(a2_, 2) + Math.pow(b2_, 2)),
					h1_ = a1_ == 0 && b1_ == 0 ? 0 : jsapi.math.deg(Math.atan2(b1_, a1_)) + (b1_ >= 0 ? 0 : 360),
					h2_ = a2_ == 0 && b2_ == 0 ? 0 : jsapi.math.deg(Math.atan2(b2_, a2_)) + (b2_ >= 0 ? 0 : 360),
					dh_cond = h2_ - h1_ > 180 ? 1 : (h2_ - h1_ < -180 ? 2 : 0),
					dh_ = dh_cond == 0 ? h2_ - h1_ : (dh_cond == 1 ? h2_ - h1_ - 360 : h2_ + 360 - h1_),
					dL_ = L2_ - L1_,
					dL = dL_,
					dC_ = C2_ - C1_,
					dC = dC_,
					dH_ = 2 * Math.sqrt(C1_ * C2_) * Math.sin(jsapi.math.rad(dh_ / 2)),
					dH = dH_,
					L__avg = jsapi.math.avg(L1_, L2_),
					C__avg = jsapi.math.avg(C1_, C2_),
					h__avg_cond = C1_ * C2_ == 0 ? 3 : (Math.abs(h2_ - h1_) <= 180 ? 0 : (h2_ + h1_ < 360 ? 1 : 2)),
					h__avg = h__avg_cond == 3 ? h1_ + h2_ : (h__avg_cond == 0 ? jsapi.math.avg(h1_, h2_) : (h__avg_cond == 1 ? jsapi.math.avg(h1_, h2_) + 180 : jsapi.math.avg(h1_, h2_) - 180)),
					AB = Math.pow(L__avg - 50, 2),	// (L'_ave-50)^2
					S_L = 1 + .015 * AB / Math.sqrt(20 + AB),
					S_C = 1 + .045 * C__avg,
					T = 1 - .17 * Math.cos(jsapi.math.rad(h__avg - 30)) + .24 * Math.cos(jsapi.math.rad(2 * h__avg)) + .32 * Math.cos(jsapi.math.rad(3 * h__avg + 6))
						- .2 * Math.cos(jsapi.math.rad(4 * h__avg - 63)),
					S_H = 1 + .015 * C__avg * T,
					dTheta = 30 * Math.exp(-1 * Math.pow((h__avg - 275) / 25, 2)),
					R_C = 2 * Math.sqrt(Math.pow(C__avg, 7) / (Math.pow(C__avg, 7) + pow25_7)),
					R_T = -Math.sin(jsapi.math.rad(2 * dTheta)) * R_C,
					AJ = dL_ / S_L / k_L,	// dL' / k_L / S_L
					AK = dC_ / S_C / k_C,	// dC' / k_C / S_C
					AL = dH_ / S_H / k_H,	// dH' / k_H / S_H
					dE = Math.sqrt(Math.pow(AJ, 2) + Math.pow(AK, 2) + Math.pow(AL, 2) + R_T * AK * AL);
				
				if (debug) {
					r = (C1 + "|" + C2 + "|" + C_avg + "|" + G + "|" + L1_ + "|" + a1_ + "|" + b1_ + "|" + L2_ + "|" + a2_ + "|" + b2_ + "|" + C1_ + "|" + C2_ + "|" + h1_ + "|" + h2_ + "|" + dh_ + "|" + dL_ + "|" + dC_ + "|" + dH_ + "|" + L__avg + "|" + C__avg + "|" + h__avg + "|" + AB + "|" + S_L + "|" + S_C + "|" + T + "|" + S_H + "|" + dTheta + "|" + R_C + "|" + R_T + "|" + AJ + "|" + AK + "|" + AL + "|" + dE + "|" + dh_cond + "|" + h__avg_cond).split("|");
					alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
					t = [];
					n = alpha.indexOf("G");
					for (i = 0; i < r.length; i ++) {
						a = i + n < alpha.length ? alpha[i + n] : "A" + alpha[i + n - alpha.length];
						t.push(a + ": " + r[i]);
					}
					return t.join("\n");
				};
				
				break;
			default:
				var dL = L1 - L2,
					C1 = Math.sqrt(Math.pow(a1, 2) + Math.pow(b1, 2)),
					C2 = Math.sqrt(Math.pow(a2, 2) + Math.pow(b2, 2)),
					dC = C1 - C2,
					dH = Math.sqrt(Math.round((Math.pow(a1 - a2, 2) + Math.pow(b1 - b2, 2) - Math.pow(dC, 2))*100000000000000)/100000000000000),
					// this is merely a bugfix for browser quirks experienced in mozilla:
					//dH = isNaN(dH) ? Math.sqrt(Math.pow(a1 - a2, 2) + Math.pow(b1 - b2, 2) - Math.round(Math.pow(dC, 2)*100000000000000)/100000000000000) : dH,
					dE = Math.sqrt(Math.pow(dL, 2) + Math.pow(a1 - a2, 2) + Math.pow(b1 - b2, 2));
					if (isNaN(dH)) {
						if (window.location.href.indexOf("?debug")>-1) alert('a1: ' + a1 + '\na2: ' + a2 + '\nMath.pow(a1 - a2, 2): ' + Math.pow(a1 - a2, 2) + '\nb1: ' + b1 + '\nb2: ' + b2 + '\nMath.pow(b1 - b2, 2): ' + Math.pow(b1 - b2, 2) + '\ndC: ' + dC + '\nMath.pow(dC, 2): ' + Math.pow(dC, 2) + '\nMath.pow(a1 - a2, 2) + Math.pow(b1 - b2, 2) - Math.pow(dC, 2): ' + (Math.pow(a1 - a2, 2) + Math.pow(b1 - b2, 2) - Math.pow(dC, 2)));
					}
		};
		
		return {
			E: dE,
			L: dL,
			C: dC,
			H: dH
		};
	};
