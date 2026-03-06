using Microsoft.Extensions.Configuration;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

if (args.Length == 0)
{
    PrintUsage();
    return 1;
}

var config = new ConfigurationBuilder()
    .SetBasePath(System.AppContext.BaseDirectory)
    .AddJsonFile("appsettings.json", optional: false)
    .Build();

var dv = config.GetSection("Dataverse");
string connectionString =
    "AuthType=ClientSecret;" +
    $"Url={dv["Url"]};" +
    $"ClientId={dv["ClientId"]};" +
    $"ClientSecret={dv["ClientSecret"]}";

try
{
    using ServiceClient serviceClient = new(connectionString);

    if (!serviceClient.IsReady)
    {
        Console.WriteLine($"Error: Failed to connect to Dataverse: {serviceClient.LastError}");
        return 1;
    }

    return args[0].ToLower() switch
    {
        "create-incident" => CreateIncident(serviceClient, args[1..]),
        "get-opportunity-value" => GetOpportunityValue(serviceClient),
        "create-legoset" => CreateLegoSet(serviceClient, args[1..]),
        "get-legoset" => GetLegoSet(serviceClient, args[1..]),
        "list-legosets" => ListLegoSets(serviceClient),
        "update-legoset" => UpdateLegoSet(serviceClient, args[1..]),
        "delete-legoset" => DeleteLegoSet(serviceClient, args[1..]),
        "add-note" => AddNote(serviceClient, args[1..]),
        _ => PrintUsage()
    };
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
    if (ex.InnerException != null)
        Console.WriteLine($"Details: {ex.InnerException.Message}");
    return 1;
}

static int PrintUsage()
{
    Console.WriteLine("Usage: DataverseTool <command> [options]");
    Console.WriteLine();
    Console.WriteLine("Commands:");
    Console.WriteLine("  create-incident --title <title> --description <desc> --origin <origin> --priority <priority> --customer <name>");
    Console.WriteLine("    origin:   Phone, Email, Web, IoT");
    Console.WriteLine("    priority: High, Normal, Low");
    Console.WriteLine();
    Console.WriteLine("  get-opportunity-value");
    Console.WriteLine();
    Console.WriteLine("LEGO Set commands:");
    Console.WriteLine("  create-legoset --name <name> --number <number> --pieces <count> --image <path>");
    Console.WriteLine("  get-legoset --number <number>");
    Console.WriteLine("  list-legosets");
    Console.WriteLine("  update-legoset --number <number> [--name <name>] [--pieces <count>] [--image <path>]");
    Console.WriteLine("  delete-legoset --number <number>");
    Console.WriteLine("  add-note --number <number> --subject <subject> --text <text> [--image <path>]");
    return 1;
}

static int CreateIncident(ServiceClient serviceClient, string[] args)
{
    string? title = null, description = null, customer = null;
    string? origin = null, priority = null;

    for (int i = 0; i < args.Length - 1; i += 2)
    {
        switch (args[i].ToLower())
        {
            case "--title": title = args[i + 1]; break;
            case "--description": description = args[i + 1]; break;
            case "--origin": origin = args[i + 1]; break;
            case "--priority": priority = args[i + 1]; break;
            case "--customer": customer = args[i + 1]; break;
        }
    }

    if (title is null || description is null || origin is null || priority is null || customer is null)
    {
        Console.WriteLine("Error: All parameters are required: --title, --description, --origin, --priority, --customer");
        return 1;
    }

    int caseOriginCode = origin.ToLower() switch
    {
        "phone" => 1,
        "email" => 2,
        "web" => 3,
        "iot" => 700610000,
        _ => throw new InvalidOperationException($"Invalid origin '{origin}'. Use: Phone, Email, Web, IoT")
    };

    int priorityCode = priority.ToLower() switch
    {
        "high" => 1,
        "normal" => 2,
        "low" => 3,
        _ => throw new InvalidOperationException($"Invalid priority '{priority}'. Use: High, Normal, Low")
    };

    QueryExpression contactQuery = new("contact")
    {
        ColumnSet = new ColumnSet("contactid", "fullname"),
        TopCount = 1,
        Criteria = new FilterExpression(LogicalOperator.And)
        {
            Conditions =
            {
                new ConditionExpression("fullname", ConditionOperator.Like, $"%{customer}%")
            }
        }
    };

    EntityCollection contacts = serviceClient.RetrieveMultiple(contactQuery);

    if (contacts.Entities.Count == 0)
    {
        Console.WriteLine($"Error: No contact found matching '{customer}'.");
        return 1;
    }

    Entity contact = contacts.Entities[0];
    Console.WriteLine($"Found contact: {contact.GetAttributeValue<string>("fullname")} ({contact.Id})");

    Entity incident = new("incident");
    incident["title"] = title;
    incident["description"] = description;
    incident["caseorigincode"] = new OptionSetValue(caseOriginCode);
    incident["prioritycode"] = new OptionSetValue(priorityCode);
    incident["customerid"] = new EntityReference("contact", contact.Id);

    Guid incidentId = serviceClient.Create(incident);
    Console.WriteLine($"Incident created. ID: {incidentId}");
    return 0;
}

static int GetOpportunityValue(ServiceClient serviceClient)
{
    QueryExpression query = new("opportunity")
    {
        ColumnSet = new ColumnSet("estimatedvalue")
    };

    EntityCollection opportunities = serviceClient.RetrieveMultiple(query);

    decimal totalValue = 0;
    foreach (Entity opp in opportunities.Entities)
    {
        Money? value = opp.GetAttributeValue<Money>("estimatedvalue");
        if (value != null)
            totalValue += value.Value;
    }

    Console.WriteLine($"Total opportunity value: {totalValue:C}");
    Console.WriteLine($"Number of opportunities: {opportunities.Entities.Count}");
    return 0;
}

// --- LEGO Set helpers ---

static Entity? FindLegoSetByNumber(ServiceClient serviceClient, int setNumber)
{
    QueryExpression query = new("cr19f_legoset")
    {
        ColumnSet = new ColumnSet("cr19f_legosetname", "cr19f_legosetnumber", "cr19f_numberofpieces"),
        TopCount = 1,
        Criteria = new FilterExpression(LogicalOperator.And)
        {
            Conditions =
            {
                new ConditionExpression("cr19f_legosetnumber", ConditionOperator.Equal, setNumber)
            }
        }
    };
    EntityCollection results = serviceClient.RetrieveMultiple(query);
    return results.Entities.Count > 0 ? results.Entities[0] : null;
}

// --- LEGO Set commands ---

static int CreateLegoSet(ServiceClient serviceClient, string[] args)
{
    string? name = null, number = null, imagePath = null;
    string? pieces = null;

    for (int i = 0; i < args.Length - 1; i += 2)
    {
        switch (args[i].ToLower())
        {
            case "--name": name = args[i + 1]; break;
            case "--number": number = args[i + 1]; break;
            case "--pieces": pieces = args[i + 1]; break;
            case "--image": imagePath = args[i + 1]; break;
        }
    }

    if (name is null || number is null || pieces is null || imagePath is null)
    {
        Console.WriteLine("Error: All parameters are required: --name, --number, --pieces, --image");
        return 1;
    }

    Entity legoSet = new("cr19f_legoset");
    legoSet["cr19f_legosetname"] = name;
    legoSet["cr19f_legosetnumber"] = int.Parse(number);
    legoSet["cr19f_numberofpieces"] = int.Parse(pieces);
    legoSet["cr19f_boximage"] = File.ReadAllBytes(imagePath);

    Guid id = serviceClient.Create(legoSet);
    Console.WriteLine($"LEGO set created: {name} (#{number}). ID: {id}");
    return 0;
}

static int GetLegoSet(ServiceClient serviceClient, string[] args)
{
    string? number = null;
    for (int i = 0; i < args.Length - 1; i += 2)
    {
        if (args[i].ToLower() == "--number") number = args[i + 1];
    }

    if (number is null)
    {
        Console.WriteLine("Error: --number is required");
        return 1;
    }

    Entity? set = FindLegoSetByNumber(serviceClient, int.Parse(number));
    if (set is null)
    {
        Console.WriteLine($"Error: No LEGO set found with number '{number}'.");
        return 1;
    }

    Console.WriteLine($"Name:   {set.GetAttributeValue<string>("cr19f_legosetname")}");
    Console.WriteLine($"Number: {set.GetAttributeValue<int>("cr19f_legosetnumber")}");
    Console.WriteLine($"Pieces: {set.GetAttributeValue<int>("cr19f_numberofpieces")}");
    return 0;
}

static int ListLegoSets(ServiceClient serviceClient)
{
    QueryExpression query = new("cr19f_legoset")
    {
        ColumnSet = new ColumnSet("cr19f_legosetname", "cr19f_legosetnumber", "cr19f_numberofpieces")
    };

    EntityCollection results = serviceClient.RetrieveMultiple(query);

    if (results.Entities.Count == 0)
    {
        Console.WriteLine("No LEGO sets found.");
        return 0;
    }

    foreach (Entity set in results.Entities)
    {
        string setName = set.GetAttributeValue<string>("cr19f_legosetname") ?? "Unknown";
        string setNumber = set.GetAttributeValue<int>("cr19f_legosetnumber").ToString();
        int setPieces = set.GetAttributeValue<int>("cr19f_numberofpieces");
        Console.WriteLine($"  [{setNumber}] {setName} - {setPieces} pieces");
    }

    Console.WriteLine($"\nTotal: {results.Entities.Count} set(s)");
    return 0;
}

static int UpdateLegoSet(ServiceClient serviceClient, string[] args)
{
    string? number = null, name = null, imagePath = null;
    string? pieces = null;

    for (int i = 0; i < args.Length - 1; i += 2)
    {
        switch (args[i].ToLower())
        {
            case "--number": number = args[i + 1]; break;
            case "--name": name = args[i + 1]; break;
            case "--pieces": pieces = args[i + 1]; break;
            case "--image": imagePath = args[i + 1]; break;
        }
    }

    if (number is null)
    {
        Console.WriteLine("Error: --number is required");
        return 1;
    }

    Entity? existing = FindLegoSetByNumber(serviceClient, int.Parse(number));
    if (existing is null)
    {
        Console.WriteLine($"Error: No LEGO set found with number '{number}'.");
        return 1;
    }

    Entity update = new("cr19f_legoset") { Id = existing.Id };

    if (name is not null) update["cr19f_legosetname"] = name;
    if (pieces is not null) update["cr19f_numberofpieces"] = int.Parse(pieces);
    if (imagePath is not null) update["cr19f_boximage"] = File.ReadAllBytes(imagePath);

    serviceClient.Update(update);
    Console.WriteLine($"LEGO set #{number} updated.");
    return 0;
}

static int DeleteLegoSet(ServiceClient serviceClient, string[] args)
{
    string? number = null;
    for (int i = 0; i < args.Length - 1; i += 2)
    {
        if (args[i].ToLower() == "--number") number = args[i + 1];
    }

    if (number is null)
    {
        Console.WriteLine("Error: --number is required");
        return 1;
    }

    Entity? set = FindLegoSetByNumber(serviceClient, int.Parse(number));
    if (set is null)
    {
        Console.WriteLine($"Error: No LEGO set found with number '{number}'.");
        return 1;
    }

    serviceClient.Delete("cr19f_legoset", set.Id);
    Console.WriteLine($"LEGO set #{number} deleted.");
    return 0;
}

static int AddNote(ServiceClient serviceClient, string[] args)
{
    string? number = null, subject = null, text = null, imagePath = null;

    for (int i = 0; i < args.Length - 1; i += 2)
    {
        switch (args[i].ToLower())
        {
            case "--number": number = args[i + 1]; break;
            case "--subject": subject = args[i + 1]; break;
            case "--text": text = args[i + 1]; break;
            case "--image": imagePath = args[i + 1]; break;
        }
    }

    if (number is null || subject is null || text is null)
    {
        Console.WriteLine("Error: --number, --subject, and --text are required");
        return 1;
    }

    Entity? set = FindLegoSetByNumber(serviceClient, int.Parse(number));
    if (set is null)
    {
        Console.WriteLine($"Error: No LEGO set found with number '{number}'.");
        return 1;
    }

    string noteHtml = $"<div class=\"ck-content\" data-wrapper=\"true\" dir=\"ltr\" " +
        "style=\"--ck-image-style-spacing: 1.5em; --ck-inline-image-style-spacing: calc(var(--ck-image-style-spacing) / 2); " +
        "font-family: Segoe UI; font-size: 11pt;\">";

    if (imagePath is not null)
    {
        // Create msdyn_richtextfile record with parent metadata
        byte[] fileBytes = File.ReadAllBytes(imagePath);
        Entity rtFile = new("msdyn_richtextfile");
        rtFile["msdyn_parententity_fieldname"] = "notetext";
        rtFile["msdyn_parententityname"] = "cr19f_legoset";
        rtFile["msdyn_parentid"] = set.Id.ToString();
        Guid rtFileId = serviceClient.Create(rtFile);

        // Set the image blob via update
        Entity rtUpdate = new("msdyn_richtextfile") { Id = rtFileId };
        rtUpdate["msdyn_imageblob"] = fileBytes;
        serviceClient.Update(rtUpdate);
        Console.WriteLine($"Uploaded rich text image. ID: {rtFileId}");

        noteHtml += $"<p style=\"margin: 0;\"><img src=\"/api/data/v9.0/msdyn_richtextfiles({rtFileId})/msdyn_imageblob/$value?size=full\"></p>";
    }

    noteHtml += $"<p style=\"margin: 0;\">{System.Net.WebUtility.HtmlEncode(text)}</p></div>";

    Entity note = new("annotation");
    note["objectid"] = new EntityReference("cr19f_legoset", set.Id);
    note["subject"] = subject;
    note["notetext"] = noteHtml;

    Guid noteId = serviceClient.Create(note);
    Console.WriteLine($"Note added. ID: {noteId}");

    return 0;
}

