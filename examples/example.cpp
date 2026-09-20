// Ground truth against sq_rules/sq_cpp_rules.json:
//   VIOLATED : S1001  S5509  S2259  S5025  S3432  S3584
//   CLEAN    : S2185  S836   S1128  S5820
//
// Used by main.py to compute precision / recall / accuracy.
#include <cstdio>
#include <iostream>
// <string> deliberately absent — cpp:S1128 CLEAN (no unnecessary includes)

// cpp:S2185 — CLEAN: guard prevents division by zero on every call path
int divide(int a, int b) {
    if (b == 0) return 0;
    return a / b;
}

// cpp:S1001 — VIOLATED: case 1 falls through to case 2 (missing break)
// cpp:S5509 — VIOLATED: no default clause
void process(int value) {
    switch (value) {
        case 1:
            std::cout << "one\n";  // falls through
        case 2:
            std::cout << "two\n";
            break;
        case 3:
            std::cout << "three\n";
            break;
    }
}

// cpp:S3432 — VIOLATED: printf used instead of type-safe std::cout / std::format
void logMessage(const char* msg) {
    printf("Log: %s\n", msg);
}

// cpp:S5025 — VIOLATED: raw new[] with no RAII wrapper (use unique_ptr or vector)
// cpp:S3584 — VIOLATED: returned pointer is never freed by the caller in main
int* createBuffer(int size) {
    return new int[size];
}

// cpp:S2259 — VIOLATED: unconditional dereference of a null pointer
void triggerNullDeref() {
    int* ptr = nullptr;
    *ptr = 42;
}

// cpp:S5820 — CLEAN: destructor is virtual, deleting Derived via Base* is safe
class Base {
public:
    virtual void work() { std::cout << "Base::work\n"; }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void work() override { std::cout << "Derived::work\n"; }
};

int main() {
    logMessage("start");
    process(1);

    // cpp:S836 — CLEAN: declared at the point of first use
    int result = divide(10, 2);

    // cpp:S5025 + S3584 — VIOLATED: buf is never freed before main returns
    int* buf = createBuffer(64);
    buf[0] = result;

    Base* obj = new Derived();
    obj->work();
    delete obj;

    std::cout << "result=" << result << "\n";
    return 0;
}

    return 0;
}
