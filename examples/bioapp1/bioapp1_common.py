# Copyright 2013 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

from devsim import (
    contact_equation,
    contact_node_model,
    cylindrical_edge_couple,
    cylindrical_node_volume,
    edge_from_node_model,
    edge_model,
    element_from_edge_model,
    equation,
    get_dimension,
    get_material,
    get_node_model_values,
    get_region_list,
    interface_equation,
    interface_model,
    node_model,
    node_solution,
    set_node_values,
    set_parameter,
)

#### molarity 0.001 mole / Liter * 1 L / (1e3 cm^3) * 6.02e23 / mole = 6.02e17 /cm^3
set_parameter(device="disk", region="solution", name="n_bound", value=6.02e17)
#### 2q/nm^3 -->  2/nm^3 * (1 nm^3/(1e-7 cm)^3)
# set_parameter device="disk", region="dna",        name="charge_density", value=0,
set_parameter(device="disk", region="dna", name="charge_density", value=2e21)
set_parameter(device="disk", region="dielectric", name="charge_density", value=0)

dimension = get_dimension(device="disk")

material_parameter_table = (
    {
        "material": "global",
        "parameter": "q",
        "value": 1.6e-19,
        "unit": "coul",
        "description": "Charge of an electron",
    },
    {
        "material": "ionic_solution",
        "parameter": "mu_c",
        "value": 7.62e-4,
        "unit": "cm^2/(V*sec)",
        "description": "mobility of cations (K+)",
    },
    {
        "material": "ionic_solution",
        "parameter": "mu_a",
        "value": 7.98e-4,
        "unit": "cm^2/(V*sec)",
        "description": "mobility of anions (Cl-)",
    },
    {
        "material": "ionic_solution",
        "parameter": "Permittivity",
        "value": 80 * 8.85e-14,
        "unit": "F/cm",
        "description": "",
    },
    {
        "material": "dielectric",
        "parameter": "Permittivity",
        "value": 3 * 8.85e-14,
        "unit": "F/cm",
        "description": "",
    },
    {
        "material": "dna",
        "parameter": "Permittivity",
        "value": 4 * 8.85e-14,
        "unit": "F/cm",
        "description": "",
    },
)

material_parameters = {}

for m in material_parameter_table:
    material_parameters[m["material"]] = {}
for m in material_parameter_table:
    material_parameters[m["material"]][m["parameter"]] = m["value"]

for k, v in material_parameters["global"].items():
    set_parameter(device="disk", name=k, value=v)

for r in get_region_list(device="disk"):
    m = get_material(device="disk", region=r)
    for k, v in material_parameters[m].items():
        set_parameter(device="disk", region=r, name=k, value=v)

set_parameter(device="disk", region="solution", name="V_t", value=0.0238)

for region in ("dna", "dielectric", "solution"):
    node_solution(device="disk", region=region, name="Potential")
    edge_from_node_model(device="disk", region=region, node_model="Potential")

    if dimension == 2:
        set_parameter(device="disk", name="raxis_variable", value="x")
        set_parameter(device="disk", name="raxis_zero", value=0)
        cylindrical_node_volume(device="disk", region=region)
        cylindrical_edge_couple(device="disk", region=region)

        set_parameter(name="node_volume_model", value="CylindricalNodeVolume")
        set_parameter(name="edge_couple_model", value="CylindricalEdgeCouple")
        set_parameter(
            name="element_edge_couple_model", value="ElementCylindricalEdgeCouple"
        )
        set_parameter(
            name="element_node0_volume_model", value="ElementCylindricalNodeVolume@en0"
        )
        set_parameter(
            name="element_node1_volume_model", value="ElementCylindricalNodeVolume@en1"
        )

        x = sum(
            get_node_model_values(
                device="disk", region=region, name="CylindricalNodeVolume"
            )
        )
        y = sum(get_node_model_values(device="disk", region=region, name="NodeVolume"))
        print("Volume {0} {1} {2}".format(region, x, y))
    else:
        y = sum(get_node_model_values(device="disk", region=region, name="NodeVolume"))
        print("Volume {0} {1}".format(region, y))

    # Electric Field Edge Model
    edge_model(
        device="disk",
        region=region,
        name="EField",
        equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
    )

    edge_model(
        device="disk",
        region=region,
        name="EField:Potential@n0",
        equation="EdgeInverseLength",
    )

    edge_model(
        device="disk",
        region=region,
        name="EField:Potential@n1",
        equation="-EdgeInverseLength",
    )

    edge_model(
        device="disk", region=region, name="DField", equation="Permittivity*EField"
    )
    edge_model(
        device="disk",
        region=region,
        name="DField:Potential@n0",
        equation="Permittivity*EField:Potential@n0",
    )
    edge_model(
        device="disk",
        region=region,
        name="DField:Potential@n1",
        equation="Permittivity*EField:Potential@n1",
    )

# create anions and cations solution variable in solution (positive only applied in equation)
node_solution(device="disk", region="solution", name="cations")
edge_from_node_model(device="disk", region="solution", node_model="cations")
node_solution(device="disk", region="solution", name="anions")
edge_from_node_model(device="disk", region="solution", node_model="anions")
node_model(device="disk", region="solution", name="small_value", equation="n_bound")
set_node_values(
    device="disk", region="solution", name="cations", init_from="small_value"
)
set_node_values(
    device="disk", region="solution", name="anions", init_from="small_value"
)

# create Poisson equation in each region
# sign is negative since poisson equation all on lhs
node_model(
    device="disk", region="solution", name="NetCharge", equation="q*(anions - cations)"
)
node_model(device="disk", region="solution", name="NetCharge:anions", equation="q")
node_model(device="disk", region="solution", name="NetCharge:cations", equation="-q")

equation(
    device="disk",
    region="solution",
    name="PotentialEquation",
    variable_name="Potential",
    node_model="NetCharge",
    edge_model="DField",
    variable_update="default",
)


for region in ("dna", "dielectric"):
    node_model(
        device="disk", region=region, name="NetCharge", equation="-q*charge_density"
    )
    equation(
        device="disk",
        region=region,
        name="PotentialEquation",
        variable_name="Potential",
        node_model="NetCharge",
        edge_model="DField",
        variable_update="default",
    )

# create fluxes in solution
# This is complicated, but the Bernoulli functions are a representation of Sharfetter Gummel
vdiffstr = "(Potential@n0 - Potential@n1)/V_t"
edge_model(device="disk", region="solution", name="vdiff", equation=vdiffstr)
# #assuming that Potential is based on a solution, and not a model
edge_model(
    device="disk", region="solution", name="vdiff:Potential@n0", equation="V_t^(-1)"
)
edge_model(
    device="disk", region="solution", name="vdiff:Potential@n1", equation="-V_t^(-1)"
)
#
edge_model(device="disk", region="solution", name="Bern01", equation="B(vdiff)")
edge_model(
    device="disk",
    region="solution",
    name="Bern01:Potential@n0",
    equation="dBdx(vdiff) * vdiff:Potential@n0",
)
edge_model(
    device="disk",
    region="solution",
    name="Bern01:Potential@n1",
    equation="-Bern01:Potential@n0",
)
# #identity of Bernoulli functions
edge_model(device="disk", region="solution", name="Bern10", equation="Bern01 + vdiff")
edge_model(
    device="disk",
    region="solution",
    name="Bern10:Potential@n0",
    equation="Bern01:Potential@n0 + vdiff:Potential@n0",
)
edge_model(
    device="disk",
    region="solution",
    name="Bern10:Potential@n1",
    equation="Bern01:Potential@n1 + vdiff:Potential@n1",
)

Ja = " q*mu_a*EdgeInverseLength*V_t*(anions@n1*Bern10  - anions@n0*Bern01)"
edge_model(
    device="disk", region="solution", name="AnionFlux", equation="{0}".format(Ja)
)

Jc = "-q*mu_c*EdgeInverseLength*V_t*(cations@n1*Bern01 - cations@n0*Bern10)"
edge_model(
    device="disk", region="solution", name="CationFlux", equation="{0}".format(Jc)
)

# derivatives w.r.t. the solution variables
for v in (
    "Potential@n0",
    "Potential@n1",
    "anions@n0",
    "anions@n1",
    "cations@n0",
    "cations@n1",
):
    edge_model(
        device="disk",
        region="solution",
        name="AnionFlux:{0}".format(v),
        equation="simplify(diff({0},{1}))".format(Ja, v),
    )
    edge_model(
        device="disk",
        region="solution",
        name="CationFlux:{0}".format(v),
        equation="simplify(diff({0},{1}))".format(Jc, v),
    )

# create continuity equations in solution
equation(
    device="disk",
    region="solution",
    name="AnionContinuityEquation",
    variable_name="anions",
    edge_model="AnionFlux",
    variable_update="positive",
)

equation(
    device="disk",
    region="solution",
    name="CationContinuityEquation",
    variable_name="cations",
    edge_model="CationFlux",
    variable_update="positive",
)

# create n0, and potential boundary condition at contact
for contact in ("top", "bot"):
    node_model(
        device="disk",
        region="solution",
        name="{0}_potential".format(contact),
        equation="Potential - {0}_bias".format(contact),
    )
    node_model(
        device="disk",
        region="solution",
        name="{0}_potential:Potential".format(contact),
        equation="1",
    )

    contact_equation(
        device="disk",
        contact=contact,
        name="PotentialEquation",
        node_model="{0}_potential".format(contact),
        edge_charge_model="DField",
    )

    contact_node_model(
        device="disk",
        contact=contact,
        name="{0}_anion".format(contact),
        equation="anions - n_bound",
    )
    contact_node_model(
        device="disk",
        contact=contact,
        name="{0}_anion:anions".format(contact),
        equation="1",
    )
    contact_equation(
        device="disk",
        contact=contact,
        name="AnionContinuityEquation",
        node_model="{0}_anion".format(contact),
    )

    contact_node_model(
        device="disk",
        contact=contact,
        name="{0}_cation".format(contact),
        equation="cations - n_bound",
    )
    contact_node_model(
        device="disk",
        contact=contact,
        name="{0}_cation:cations".format(contact),
        equation="1",
    )
    contact_equation(
        device="disk",
        contact=contact,
        name="CationContinuityEquation",
        node_model="{0}_cation".format(contact),
    )


# create potential continuity at interfaces
for interface in ("dna_solution", "dielectric_solution"):
    interface_model(
        device="disk",
        interface=interface,
        name="continuousPotential",
        equation="Potential@r0-Potential@r1",
    )
    interface_model(
        device="disk",
        interface=interface,
        name="continuousPotential:Potential@r0",
        equation="1",
    )
    interface_model(
        device="disk",
        interface=interface,
        name="continuousPotential:Potential@r1",
        equation="-1",
    )
    interface_equation(
        device="disk",
        interface=interface,
        name="PotentialEquation",
        interface_model="continuousPotential",
        type="continuous",
    )

# For visualization
for region in ("dna", "dielectric", "solution"):
    element_from_edge_model(edge_model="EField", device="disk", region=region)
element_from_edge_model(edge_model="AnionFlux", device="disk", region="solution")
element_from_edge_model(edge_model="CationFlux", device="disk", region="solution")
