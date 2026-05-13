#include <array>
#include <cctype>
#include <cstddef>
#include <cstdlib>
#include <format>
#include <iostream>
#include <print>
#include <string>
#include <unordered_map>
#include <vector>

namespace {
// ============    asm2hack   ============ //
constexpr auto dec2bin(size_t dec) -> std::string {
    return std::format("{:016b}", dec);
}

constexpr auto tokenize(const std::string                            &line,
                        std::unordered_map<std::string, std::string> &labels)
    -> std::array<std::string, 3> {
    static size_t var_num = 16;  // NOLINT

    if (line[0] == '@') {  // @-instruction
        std::string addr = line.substr(1);

        // it's a number
        if (addr.find_last_not_of("0123456789") == std::string::npos)
            return {"@", dec2bin(std::stoi(addr)), ""};

        if (not labels.contains(addr))  // it's new variable
            labels.emplace(addr, dec2bin(var_num++));

        return {"@", labels.at(addr), ""};
    }

    // c-instruction
    size_t pos_equal     = line.find('=');
    size_t pos_semicolon = line.find(';');

    return {
        (pos_equal == -1) ? "" : line.substr(0, pos_equal),
        line.substr(pos_equal + 1, pos_semicolon - (pos_equal + 1)),
        (pos_semicolon == -1) ? "" : line.substr(pos_semicolon + 1),
    };
}

constexpr auto inst2bin(const std::array<std::string, 3> &arr) -> std::string {
    if (arr[0] == "@") return arr[1];  // @-instruction is easy

    // comp bits (with 10 non-standard symbols permutations)
    const std::unordered_map<std::string, std::string> COMP_MAP = {
        {"",    "0101010"},
        {"0",   "0101010"},
        {"1",   "0111111"},
        {"-1",  "0111010"},
        {"D",   "0001100"},
        {"A",   "0110000"},
        {"M",   "1110000"},
        {"!D",  "0001101"},
        {"!A",  "0110001"},
        {"!M",  "1110001"},
        {"-D",  "0001111"},
        {"-A",  "0110011"},
        {"-M",  "1110011"},
        {"D+1", "0011111"},
        {"1+D", "0011111"},
        {"A+1", "0110111"},
        {"1+A", "0110111"},
        {"M+1", "1110111"},
        {"1+M", "1110111"},
        {"D-1", "0001110"},
        {"A-1", "0110010"},
        {"M-1", "1110010"},
        {"D+A", "0000010"},
        {"A+D", "0000010"},
        {"D+M", "1000010"},
        {"M+D", "1000010"},
        {"D-A", "0010011"},
        {"D-M", "1010011"},
        {"A-D", "0000111"},
        {"M-D", "1000111"},
        {"D&A", "0000000"},
        {"A&D", "0000000"},
        {"D&M", "1000000"},
        {"M&D", "1000000"},
        {"D|A", "0010101"},
        {"A|D", "0010101"},
        {"D|M", "1010101"},
        {"M|D", "1010101"},
    };

    // dest bits (with 8 non-standard symbols permutations)
    const std::unordered_map<std::string, std::string> DEST_MAP = {
        {"",    "000"},
        {"M",   "001"},
        {"D",   "010"},
        {"MD",  "011"},
        {"A",   "100"},
        {"AM",  "101"},
        {"AD",  "110"},
        {"AMD", "111"},
        {"DM",  "011"},
        {"MA",  "101"},
        {"DA",  "110"},
        {"ADM", "111"},
        {"MAD", "111"},
        {"MDA", "111"},
        {"DAM", "111"},
        {"DMA", "111"},
    };

    // jump bits
    const std::unordered_map<std::string, std::string> JUMP_MAP = {
        {"",    "000"},
        {"JGT", "001"},
        {"JEQ", "010"},
        {"JGE", "011"},
        {"JLT", "100"},
        {"JNE", "101"},
        {"JLE", "110"},
        {"JMP", "111"},
    };

    return std::format("111{}{}{}", COMP_MAP.at(arr[1]), DEST_MAP.at(arr[0]),
                       JUMP_MAP.at(arr[2]));
}

constexpr auto pre_process(std::string line) -> std::string {
    line.erase(std::remove_if(line.begin(), line.end(), isspace), line.end());
    return line.substr(0, line.find_first_of("//"));
}

auto asm2hack() {
    std::string              raw;
    std::vector<std::string> lines;

    std::unordered_map<std::string, std::string> labels = {
        {"R0",     "0000000000000000"},
        {"R1",     "0000000000000001"},
        {"R2",     "0000000000000010"},
        {"R3",     "0000000000000011"},
        {"R4",     "0000000000000100"},
        {"R5",     "0000000000000101"},
        {"R6",     "0000000000000110"},
        {"R7",     "0000000000000111"},
        {"R8",     "0000000000001000"},
        {"R9",     "0000000000001001"},
        {"R10",    "0000000000001010"},
        {"R11",    "0000000000001011"},
        {"R12",    "0000000000001100"},
        {"R13",    "0000000000001101"},
        {"R14",    "0000000000001110"},
        {"R15",    "0000000000001111"},
        {"SCREEN", "0100000000000000"},
        {"KBD",    "0110000000000000"},
        {"SP",     "0000000000000000"},
        {"LCL",    "0000000000000001"},
        {"ARG",    "0000000000000010"},
        {"THIS",   "0000000000000011"},
        {"THAT",   "0000000000000100"},
    };

    // first-pass
    while (std::getline(std::cin, raw)) {
        raw = pre_process(raw);

        if (not raw.empty()) {
            if (raw[0] == '(')  // label declaration
                labels.emplace(raw.substr(1, raw.find(')') - 1),
                               dec2bin(lines.size()));
            else
                lines.push_back(raw);
        }
    }

    // second-pass
    for (const auto &line : lines) {
        std::println("{}", inst2bin(tokenize(line, labels)));
    }
}

// ============    vm2asm     ============ //
auto vm2asm() { }

// ============    jack2vm    ============ //
auto jack2vm() { }

}  // namespace

auto main(int argc, char **argv) -> int {
    if (argc != 2) {
        std::println(stderr, R"(
Usage:
    - cat file.asm | ./nand2tetris.out asm2hack > file.hack
    - cat file.jack | ./nand2tetris.out jack2vm | ./nand2tetris.out vm2asm | ./nand2tetris.out asm2hack > file.hack
        )");

        return EXIT_FAILURE;
    }

    std::string module = argv[1];  // NOLINT

    if (module == "asm2hack")
        asm2hack();
    else if (module == "vm2asm")
        vm2asm();
    else if (module == "jack2vm")
        jack2vm();
    else {
        std::println(stderr,
                     "'{}' is not a known module of nand2tetris.\n"
                     "Did you mean: 'asm2hack', 'vm2asm' or 'jack2vm'",
                     module);

        return EXIT_FAILURE;
    }

    return 0;
}
