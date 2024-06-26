/***
DEVSIM
Copyright 2013 DEVSIM LLC

SPDX-License-Identifier: Apache-2.0
***/

#include "MaterialCommands.hh"
#include "dsCommand.hh"
#include "CommandHandler.hh"
#include "GlobalData.hh"
#include "Region.hh"
#include "CheckFunctions.hh"
#include "Device.hh"
#include "Contact.hh"

#include "Validate.hh"
#include "dsAssert.hh"
#include <sstream>

using namespace dsValidate;


namespace dsCommand {
/// This is the setter/getter
void
getParameterCmd(CommandHandler &data)
{
    std::string errorString;

    const std::string commandName = data.GetCommandName();

    GlobalData &gdata = GlobalData::GetInstance();

    using namespace dsGetArgs;
    dsGetArgs::Option *option;
    if (commandName == "set_parameter")
    {
        static dsGetArgs::Option setoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"region",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"name",     "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, stringCannotBeEmpty},
            {"value",    "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, stringCannotBeEmpty},
            {nullptr,  nullptr,    dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = setoption;
    }
    else if (commandName == "get_parameter")
    {
        static dsGetArgs::Option getoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, mustBeSpecifiedIfRegionSpecified},
            {"region",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"name",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, stringCannotBeEmpty},
            {nullptr,  nullptr, dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = getoption;
    }
    else if (commandName == "get_parameter_list")
    {
        static dsGetArgs::Option getoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, mustBeSpecifiedIfRegionSpecified},
            {"region",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {nullptr,  nullptr, dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = getoption;
    }
    else if (commandName == "set_material")
    {
        static dsGetArgs::Option setoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, mustBeValidDevice},
            {"region",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"contact",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"material", "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, stringCannotBeEmpty},
            {nullptr,  nullptr,    dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = setoption;
    }
    else if (commandName == "get_material")
    {
        static dsGetArgs::Option getoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::REQUIRED, mustBeValidDevice},
            {"region",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {"contact",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr},
            {nullptr,  nullptr, dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = getoption;
    }
    else if (commandName == "get_dimension")
    {
        static dsGetArgs::Option getoption[] =
        {
            {"device",   "", dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, mustBeValidDevice},
            {nullptr,  nullptr, dsGetArgs::optionType::STRING, dsGetArgs::requiredType::OPTIONAL, nullptr}
        };
        option = getoption;
    }
    else
    {
        /// This should not be able to happen
        dsAssert(false, "UNEXPECTED");
        option = nullptr;
    }



    bool error = data.processOptions(option, errorString);

    if (error)
    {
        data.SetErrorResult(errorString);
        return;
    }

    const std::string &deviceName = data.GetStringOption("device");
    std::string regionName;
    std::string contactName;
    if (commandName != "get_dimension")
    {
      //// nasty hack
      regionName = data.GetStringOption("region");
    }

    if (commandName == "get_material" || commandName == "set_material")
    {
      contactName = data.GetStringOption("contact");
    }

    Device *dev = nullptr;
    Region *reg = nullptr;
    Contact *contact = nullptr;


    if (!regionName.empty() && !contactName.empty())
    {
      errorString += "region and contact cannot be specified at same time\n";
    }

    if (!regionName.empty() || !contactName.empty())
    {
      if (!deviceName.empty())
      {
        if (!regionName.empty())
        {
          errorString = ValidateDeviceAndRegion(deviceName, regionName, dev, reg);
        }
        else if (!contactName.empty())
        {
          errorString = ValidateDeviceAndContact(deviceName, contactName, dev, contact);
        }
      }
      else
      {
        errorString += "device must be specified when region is specified\n";
      }
    }
    else if (!deviceName.empty())
    {
        errorString = ValidateDevice(deviceName, dev);
    }

    if (!errorString.empty())
    {
        data.SetErrorResult(errorString);
        return;
    }

    if (commandName == "get_parameter")
    {
        const std::string &paramName = data.GetStringOption("name");

        GlobalData::DBEntry_t mdbentry;
        if (!deviceName.empty())
        {
          if (!regionName.empty())
          {
              mdbentry = gdata.GetDBEntryOnRegion(deviceName, regionName, paramName);
          }
          else
          {
            mdbentry = gdata.GetDBEntryOnDevice(deviceName, paramName);
          }
        }
        else
        {
            mdbentry = gdata.GetDBEntryOnGlobal(paramName);
        }

        if (mdbentry.first)
        {
            data.SetObjectResult(mdbentry.second);
        }
        else
        {
            std::ostringstream os;
            os << "Cannot find parameter \"" << paramName << "\"\n";
            errorString = os.str();
            data.SetErrorResult(errorString);
            return;
        }
    }
    else if (commandName == "get_parameter_list")
    {
      std::vector<std::string> names;
      if (!regionName.empty())
      {
        names = gdata.GetDBEntryListOnRegion(deviceName, regionName);
      }
      else if (!deviceName.empty())
      {
        names = gdata.GetDBEntryListOnDevice(deviceName);
      }
      else
      {
        names = gdata.GetDBEntryListOnGlobal();
      }

      {
        data.SetStringListResult(names);
      }
    }
    else if (commandName == "set_parameter")
    {
        const std::string &paramName = data.GetStringOption("name");

        /// Write now support only the float value for the material db
        const ObjectHolder value = data.GetObjectHolder("value");
        if (!deviceName.empty())
        {
          if (!regionName.empty())
          {
              gdata.AddDBEntryOnRegion(deviceName, regionName, paramName, value);
          }
          else
          {
              gdata.AddDBEntryOnDevice(deviceName, paramName, value);
          }
        }
        else
        {
            gdata.AddDBEntryOnGlobal(paramName, value);
        }
        data.SetEmptyResult();
    }
    else if (commandName == "set_material")
    {
      const std::string &materialName = data.GetStringOption("material");
      dsAssert(!materialName.empty(), "UNEXPECTED");
      if (reg)
      {
        reg->SetMaterial(materialName);
      }
      else if (contact)
      {
        contact->SetMaterial(materialName);
      }
      data.SetEmptyResult();
    }
    else if (commandName == "get_material")
    {

      std::string material_name;
      if (reg)
      {
         material_name = reg->GetMaterialName();
      }
      else if (contact)
      {
         material_name = contact->GetMaterialName();
      }
      data.SetStringResult(material_name);
    }
    else if (commandName == "get_dimension")
    {
      const size_t dim = dev->GetDimension();
      data.SetIntResult(dim);
    }

    return;
}

Commands MaterialCommands[] = {
    {"set_parameter", getParameterCmd},
    {"get_parameter", getParameterCmd},
    {"get_parameter_list", getParameterCmd},
    {"set_material", getParameterCmd},
    {"get_material", getParameterCmd},
    {"get_dimension",   getParameterCmd},
    {nullptr, nullptr}
};
}

