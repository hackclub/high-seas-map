CREATE TABLE similarity (shipA text references ships(id), shipB text references ships(id), value decimal);