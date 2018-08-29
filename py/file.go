// Copyright 2018 The go-python Authors.  All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// File object
//
// FIXME cpython 3.3 has a compicated heirachy of types to implement
// this which we do not emulate yet

package py

import (
	"io"
	"io/ioutil"
	"os"
)

type File os.File

var FileType = NewType("file", `represents an open file`)

func init() {
	FileType.Dict["write"] = MustNewMethod("write", func(self Object, value Object) (Object, error) {
		return self.(*File).Write(value)
	}, 0, "write(arg) -> writes the contents of arg to the file, returning the number of characters written.")

	FileType.Dict["read"] = MustNewMethod("read", func(self Object, args Tuple, kwargs StringDict) (Object, error) {
		return self.(*File).Read(args, kwargs)
	}, 0, "read([size]) -> read at most size bytes, returned as a string.\n\nIf the size argument is negative or omitted, read until EOF is reached.\nNotice that when in non-blocking mode, less data than what was requested\nmay be returned, even if no size parameter was given.")
	FileType.Dict["close"] = MustNewMethod("close", func(self Object) (Object, error) {
		return self.(*File).Close()
	}, 0, "close() -> None or (perhaps) an integer.  Close the file.\n\nSets data attribute .closed to True.  A closed file cannot be used for\nfurther I/O operations.  close() may be called more than once without\nerror.  Some kinds of file objects (for example, opened by popen())\nmay return an exit status upon closing.")
}

// Type of this object
func (o *File) Type() *Type {
	return FileType
}

func (o *File) Write(value Object) (Object, error) {
	var b []byte

	switch v := value.(type) {
	// FIXME Bytearray
	case Bytes:
		b = v

	case String:
		b = []byte(v)

	default:
		return nil, ExceptionNewf(TypeError, "expected a string or other character buffer object")
	}

	n, err := (*os.File)(o).Write(b)
	return Int(n), err
}

func (o *File) readResult(b []byte) (Object, error) {
	var asBytes = false // default mode is "as string" - also move this in File struct

	if b == nil {
		if asBytes {
			return Bytes{}, nil
		} else {
			return String(""), nil
		}
	}

	if asBytes {
		return Bytes(b), nil
	} else {
		return String(b), nil
	}
}

func (o *File) Read(args Tuple, kwargs StringDict) (Object, error) {
	var arg Object = None

	err := UnpackTuple(args, kwargs, "read", 0, 1, &arg)
	if err != nil {
		return nil, err
	}

	var r io.Reader = (*os.File)(o)

	switch pyN, ok := arg.(Int); {
	case arg == None:
		// read all

	case ok:
		// number of bytes to read
		// 0: read nothing
		// < 0: read all
		// > 0: read n
		n, _ := pyN.GoInt64()
		if n == 0 {
			return o.readResult(nil)
		}
		if n > 0 {
			r = io.LimitReader(r, n)
		}

	default:
		// invalid type
		return nil, ExceptionNewf(TypeError, "read() argument 1 must be int, not %s", arg.Type().Name)
	}

	b, err := ioutil.ReadAll(r)
	if err == io.EOF {
		return o.readResult(nil)
	}
	if err != nil {
		return nil, err
	}

	return o.readResult(b)
}

func (o *File) Close() (Object, error) {
	_ = (*os.File)(o).Close()
	return None, nil
}

func OpenFile(filename string) (Object, error) {
	f, err := os.Open(filename)
	if err != nil {
		// XXX: should check for different types of errors
		return nil, ExceptionNewf(FileNotFoundError, err.Error())
	}

	return (*File)(f), nil
}

// Check interface is satisfied
