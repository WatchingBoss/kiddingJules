import re


def solve_and_show_steps(equation_string):
    """
    Solves a simple linear equation, showing each step of the process,
    and verifies the final solution.

    This function handles equations of the form 'f(x) = c', where f(x) involves
    basic arithmetic operations (+, -, *, /). It works by reversing the
    operations on the left-hand side and applying them to the right-hand side.

    Args:
        equation_string: A string containing a simple mathematical equation.
                         Example: "(x+23)-15=10"
    """
    print(f"--- Solving the equation: {equation_string} ---\n")

    try:
        lhs, rhs_str = equation_string.split("=")
        lhs = lhs.strip()
        rhs = float(rhs_str.strip())
    except (ValueError, IndexError):
        print("Invalid equation format. Please use a format like '(x+23)-15=10'.")
        return

    steps = [f"Start: {lhs} = {rhs}"]
    inverse_op_symbol = {"+": "-", "-": "+", "*": "/", "/": "*"}

    # --- Step-by-step solving process ---

    # A robust regex to tokenize the LHS into signed terms.
    # It finds numbers or parenthesized x-expressions, with optional leading signs.
    # E.g., "53+7-x" -> ['53', '+7', '-x']
    # E.g., "21-(11+x)" -> ['21', '-(11+x)']
    terms = re.findall(r"[+\-]?\s*(?:\([^)]*x[^)]*\)|x\b|[\d\.]+)", lhs)
    terms = [t.strip().replace(" ", "") for t in terms]

    # Separate the x_term from the other terms that need to be moved.
    x_term = None
    other_terms = []
    for term in terms:
        if "x" in term:
            x_term = term
        else:
            other_terms.append(term)

    if x_term is None:
        print("Could not find 'x' in the equation.")
        return

    # Part 1: Move all non-x terms to the RHS, isolating the x_term.
    # Process terms from right to left to match the expected output's logic.
    for term in reversed(other_terms):
        op_match = re.match(r"([+\-*/])\s*([\d\.]+)", term)
        if op_match:
            op, num_str = op_match.groups()
            num = float(num_str)
        else:
            # First term might not have a sign, e.g., "53" is treated as "+53"
            op = "+"
            num = float(term)

        inverse_op = inverse_op_symbol[op]
        step_description = (
            f"Undo '{term}': Move to other side as '{inverse_op}{num}'"
        )
        if term.startswith("+"):
            step_description = (
                f"Undo '{term[1:]}': Move to other side as '{inverse_op}{num}'"
            )
        elif op == "+" and not term.startswith("-"):
            step_description = (
                f"Undo '{term}': Subtract {term} from both sides"
            )


        steps.append(step_description)
        new_rhs_str = f"{rhs} {inverse_op} {num}"

        if op == "+": rhs -= num
        elif op == "-": rhs += num
        elif op == "*": rhs /= num
        elif op == "/": rhs *= num

        steps.append(f"{x_term} = {new_rhs_str}  =>  {x_term} = {rhs}")

    # Handle negation on the x_term itself, e.g., "-x" or "-(11+x)"
    if x_term.startswith("-"):
        step_description = "Undo negation: Multiply both sides by -1"
        steps.append(step_description)
        rhs *= -1
        x_term = x_term[1:]  # Remove the leading '-'
        steps.append(f"{x_term} = {rhs}")

    # Part 2: Handle operations inside the x_term (if it's in parentheses).
    if "(" in x_term:
        inner_x_group = x_term.replace("(", "").replace(")", "").strip()

        # Tokenize the inner expression, e.g., "11+x" -> ['11', '+', 'x']
        components = re.findall(r"[+\-*/]|[\d\.]+|x", inner_x_group)

        if len(components) == 3:
            if components[0] == 'x':  # Case: x op num, e.g., x+23
                op, num_str = components[1], components[2]
                num = float(num_str)
                inverse_op = inverse_op_symbol[op]

                step_description = f"Isolate x: Move '{op}{num}' to other side as '{inverse_op}{num}'"
                steps.append(step_description)
                new_rhs_str = f"{rhs} {inverse_op} {num}"

                if op == "+": rhs -= num
                elif op == "-": rhs += num
                elif op == "*": rhs /= num
                elif op == "/": rhs *= num

                steps.append(f"x = {new_rhs_str}  =>  x = {rhs}")

            elif components[2] == 'x':  # Case: num op x, e.g., 15+x
                num_str, op = components[0], components[1]
                num = float(num_str)

                if op == '+': # e.g., 15+x=RHS -> x=RHS-15
                    inverse_op = inverse_op_symbol[op]
                    step_description = f"Isolate x: Move '+{num}' to other side as '{inverse_op}{num}'"
                    steps.append(step_description)
                    new_rhs_str = f"{rhs} {inverse_op} {num}"
                    rhs -= num
                    steps.append(f"x = {new_rhs_str}  =>  x = {rhs}")

                elif op == '-': # e.g., 15-x=RHS -> -x=RHS-15 -> x=15-RHS
                    step_description = f"Undo '{num}-...': First, subtract {num}"
                    steps.append(step_description)
                    new_rhs_str = f"{rhs} - {num}"
                    rhs -= num
                    steps.append(f"-x = {new_rhs_str}  =>  -x = {rhs}")

                    step_description = "Undo negation: Multiply both sides by -1"
                    steps.append(step_description)
                    rhs *= -1
                    steps.append(f"x = {rhs}")

    final_x = rhs
    print("--- Procedure ---")
    print("\n".join(steps))
    print(f"\nFinal Answer: x = {final_x}")

    # --- Verification ---
    print("\n--- Verification ---")
    verification_lhs_str = equation_string.split("=")[0].strip()
    verification_lhs_subbed = verification_lhs_str.replace("x", str(final_x))

    try:
        eval_result = eval(verification_lhs_subbed)
        original_rhs = float(equation_string.split("=")[1].strip())

        print(f"Substitute x = {final_x} into the left side: {verification_lhs_subbed}")
        print(f"Calculated LHS value: {eval_result}")
        print(f"Original RHS value:   {original_rhs}")

        if abs(eval_result - original_rhs) < 1e-9:
            print("\nResult: The solution is correct.")
        else:
            print("\nResult: The solution is incorrect.")
    except Exception as e:
        print(f"Could not automatically verify the solution. Error: {e}")
    print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    solve_and_show_steps("(x+23)-15=10")
    solve_and_show_steps("21-(11+x)=30")
    solve_and_show_steps("(15+x)-10=12")
    solve_and_show_steps("53+7-x=20")