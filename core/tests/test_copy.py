from compone import Component


@Component
def MyComp(*, a):
    elemlist = ", ".join(str(e) for e in a)
    return f"Some component {elemlist}"


def test_old_instance_not_affected_on_append():
    comp1 = MyComp(a=[1, 2, 3])
    comp2 = comp1.append(a=[4])

    assert str(comp1) == "Some component 1, 2, 3"
    assert str(comp2) == "Some component 1, 2, 3, 4"

    comp3 = comp2.append(a=[6])
    assert str(comp2) == "Some component 1, 2, 3, 4"
    assert str(comp3) == "Some component 1, 2, 3, 4, 6"


def test_old_instance_not_affected_on_replace():
    arg1 = [1, 2, 3]
    comp1 = MyComp(a=arg1)
    comp2 = comp1.replace(a=[4])
    arg1.append(4)

    assert str(comp1) == "Some component 1, 2, 3, 4"
    assert str(comp2) == "Some component 4"
