from control_trace import Guard, ControlMissing


def validate_data():
    print('Validated input')
    return True


def review_result():
    print('Reviewed output')
    return True


guard = Guard(['validate', 'review'], work_id='demo')
guard.run('validate', validate_data)
guard.run('review', review_result)
try:
    print('Published:', guard.finalize({'answer': 42}))
except ControlMissing as error:
    print('Blocked:', error.missing)
